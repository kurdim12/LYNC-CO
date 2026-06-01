#
# LIV — Lynk & Co Conversational Avatar — Phase 0 spike
#
# A streaming voice+face agent: headset mic -> Deepgram STT -> LLM (Liv persona +
# 08 knowledge) -> ElevenLabs TTS -> Simli lip-synced face -> local WebRTC display.
#
# ─────────────────────────────────────────────────────────────────────────────
# API NOTE (read DOCUMENTATION.md §5, §20): Pipecat's API drifts between releases.
# Everything below was VERIFIED against the *installed* package — Pipecat 1.3.0 —
# by introspection and by scaffolding the CLI's known-good baseline, NOT assumed
# from older docs. Notable 1.x facts this file depends on:
#   • VAD is wired into the user aggregator (LLMUserAggregatorParams(vad_analyzer=...)),
#     NOT TransportParams and NOT a standalone VADProcessor.
#   • Interruptions / barge-in are ON by default (there is no allow_interruptions flag).
#   • Service config uses settings=Service.Settings(...); direct voice_id=/model=/
#     live_options= kwargs are deprecated.
#   • PipelineTask is deprecated -> use PipelineWorker; run via WorkerRunner.
#   • The dev runner discovers an async `bot(runner_args)` entrypoint and serves the
#     local WebRTC signaling + a prebuilt test client at http://localhost:7860.
# If you bump pipecat-ai, re-run `python smoke_test.py` before trusting this file.
# ─────────────────────────────────────────────────────────────────────────────
#
# Run (after `cp .env.example .env` and filling keys):
#     python bot.py
# then open http://localhost:7860 and talk to Liv.

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.observers.loggers.metrics_log_observer import MetricsLogObserver
from pipecat.observers.loggers.transcription_log_observer import TranscriptionLogObserver
from pipecat.observers.loggers.llm_log_observer import LLMLogObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments, SmallWebRTCRunnerArguments
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.workers.runner import WorkerRunner

load_dotenv(override=True)

# ── Logging ──────────────────────────────────────────────────────────────────
# Verbose frame logging via LOG_LEVEL=DEBUG (DOCUMENTATION.md §19's "--debug").
logger.remove()
logger.add(sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"))

ROOT = Path(__file__).resolve().parent


# ── System prompt = Liv persona + 08 knowledge (DOCUMENTATION.md §6.3, §7) ─────
def load_system_prompt() -> str:
    """Concatenate the persona and the car knowledge base into one system message.

    These are Liv's brain and her ONLY source of car facts. We fail loudly if either
    is missing — running Liv without her guardrails/knowledge is never what we want.
    """
    persona_path = ROOT / "prompts" / "liv_persona_v1.md"
    knowledge_path = ROOT / "knowledge" / "lynkco_08.md"
    missing = [str(p) for p in (persona_path, knowledge_path) if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required prompt/knowledge file(s): {missing}")

    persona = persona_path.read_text(encoding="utf-8").strip()
    knowledge = knowledge_path.read_text(encoding="utf-8").strip()
    return (
        f"{persona}\n\n"
        "═══════════════════════════════════════════════════════════════════════\n"
        "# CAR FACTS (your ONLY source of specs/prices — never go beyond this)\n"
        "═══════════════════════════════════════════════════════════════════════\n\n"
        f"{knowledge}"
    )


# ── LLM brain: provider A/B (DOCUMENTATION.md §6.3, §16) ───────────────────────
# Default GPT-4o; swap to Gemini Flash or Claude in the spike via env to judge
# Arabic naturalness + latency, then lock the winner. Imports are lazy so a missing
# optional extra only matters if you actually select that provider.
def create_llm():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        from pipecat.services.openai.llm import OpenAILLMService

        model = os.getenv("LLM_MODEL", "gpt-4o")
        logger.info(f"LLM: OpenAI / {model}")
        return OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            settings=OpenAILLMService.Settings(model=model),
        )

    if provider == "anthropic":
        from pipecat.services.anthropic.llm import AnthropicLLMService

        model = os.getenv("LLM_MODEL", "claude-sonnet-4-5")
        logger.info(f"LLM: Anthropic / {model}")
        return AnthropicLLMService(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            settings=AnthropicLLMService.Settings(model=model),
        )

    if provider in ("google", "gemini"):
        from pipecat.services.google.llm import GoogleLLMService

        model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
        logger.info(f"LLM: Google / {model}")
        return GoogleLLMService(
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            settings=GoogleLLMService.Settings(model=model),
        )

    raise ValueError(f"Unknown LLM_PROVIDER={provider!r} (use openai | anthropic | google)")


# ── Startup readiness (helps debug "nothing happens") ─────────────────────────
def _log_env_readiness() -> list[str]:
    """Log which keys are present (never the values); return the list of MISSING required keys."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    llm_key = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GEMINI_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider, "OPENAI_API_KEY")
    mark = lambda n: "set" if os.getenv(n) else "MISSING"  # noqa: E731
    logger.info(
        f"Keys → DEEPGRAM:{mark('DEEPGRAM_API_KEY')}  {provider}:{mark(llm_key)}  "
        f"ELEVENLABS:{mark('ELEVENLABS_API_KEY')}  VOICE_ID:{mark('ELEVENLABS_VOICE_ID')}  "
        f"SIMLI:{mark('SIMLI_API_KEY')}  FACE_ID:{mark('SIMLI_FACE_ID')}"
    )
    required = ["DEEPGRAM_API_KEY", llm_key, "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]
    return [n for n in required if not os.getenv(n)]


# ── The pipeline (DOCUMENTATION.md §6.6) ───────────────────────────────────────
async def run_bot(transport: BaseTransport):
    logger.info("Starting Liv …")
    missing = _log_env_readiness()
    if missing:
        logger.error(
            "✗ Missing required key(s) in .env: "
            + ", ".join(missing)
            + ".  Liv can't start. Put them in a file named exactly '.env' (same folder as "
            "bot.py), one per line like  DEEPGRAM_API_KEY=xxxx  — then reconnect. "
            "(Watch out: it must be '.env', not '.env.txt' or '.env.example'.)"
        )
        return

    # STT — Deepgram Nova-3, Levantine + EN code-switch (§6.2).
    # NOTE: confirm in the spike that Nova-3 'multi' actually covers Jordanian Arabic;
    # if not, set DEEPGRAM_LANGUAGE=ar (trades off EN code-switch). interim_results +
    # endpointing keep turn-taking snappy.
    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        settings=DeepgramSTTService.Settings(
            model=os.getenv("DEEPGRAM_MODEL", "nova-3"),
            language=os.getenv("DEEPGRAM_LANGUAGE", "multi"),
            interim_results=True,
            smart_format=True,
            punctuate=True,
        ),
    )

    # LLM — Liv's brain (provider chosen via env).
    llm = create_llm()

    # TTS — ElevenLabs Flash v2.5 multilingual, tuned expressive (§6.4, §9, §20).
    # Lower stability + some style = "into it", not flat. Tune in the spike.
    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        settings=ElevenLabsTTSService.Settings(
            voice=os.getenv("ELEVENLABS_VOICE_ID"),
            model=os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5"),
            stability=float(os.getenv("ELEVENLABS_STABILITY", "0.4")),
            style=float(os.getenv("ELEVENLABS_STYLE", "0.6")),
            use_speaker_boost=True,
        ),
    )

    # Face — Simli (Trinity). MUST come after TTS so it lip-syncs the audio (§6.5, §20).
    # IMPORTANT: Simli sits between TTS and the output, so a missing/invalid SIMLI_FACE_ID
    # blocks the AUDIO too → the classic "nothing happens". So we only add the face when it
    # is actually configured (and DISABLE_FACE isn't set); otherwise Liv runs AUDIO-ONLY and
    # you still hear her — which isolates whether the problem is the face or the pipeline.
    video = None
    if os.getenv("DISABLE_FACE", "").lower() in ("1", "true", "yes"):
        logger.warning("DISABLE_FACE set → AUDIO-ONLY (no Simli face).")
    elif os.getenv("SIMLI_API_KEY") and os.getenv("SIMLI_FACE_ID"):
        from pipecat.services.simli.video import SimliVideoService

        is_trinity = os.getenv("SIMLI_TRINITY", "true").lower() in ("1", "true", "yes")
        video = SimliVideoService(
            api_key=os.getenv("SIMLI_API_KEY"),
            face_id=os.getenv("SIMLI_FACE_ID"),
            is_trinity_avatar=is_trinity,
        )
        logger.info("Simli face enabled.")
    else:
        logger.warning(
            "SIMLI_API_KEY/SIMLI_FACE_ID not set → AUDIO-ONLY (no face). Create a Simli face "
            "and set SIMLI_FACE_ID to see Liv's face (Phase 1)."
        )

    # Context: system message (persona + knowledge) seeds the conversation (§6.3).
    context = LLMContext(messages=[{"role": "system", "content": load_system_prompt()}])
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        # In Pipecat 1.x the VAD analyzer lives here (drives turn-taking + barge-in).
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    # Streaming/overlapping loop: each stage feeds the next (§3, §6.6).
    stages = [
        transport.input(),      # mic in (local WebRTC, VAD)
        stt,                    # speech -> text
        user_aggregator,        # add user turn to context
        llm,                    # Liv thinks (streams tokens)
        tts,                    # text -> expressive audio (starts on sentence 1)
    ]
    if video is not None:
        stages.append(video)    # audio -> lip-synced face
    stages += [
        transport.output(),     # video + audio out to the display
        assistant_aggregator,   # add Liv's turn to context
    ]
    pipeline = Pipeline(stages)

    # Metrics give us per-stage TTFB; PipelineWorker also auto-attaches a
    # UserBotLatencyObserver for perceived end-to-end latency (§13, Phase 0 gate).
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        observers=[
            TranscriptionLogObserver(),  # logs what Liv HEARS (STT) — see if your mic lands
            LLMLogObserver(),            # logs what Liv THINKS/replies (LLM)
            MetricsLogObserver(),        # per-stage latency / TTFB
        ],
        # Release Simli minutes when nobody's talking (§6.5, §12, §15).
        idle_timeout_secs=float(os.getenv("IDLE_TIMEOUT_SECS", "300")),
    )

    # Liv opens the conversation when a guest connects (the attract moment, §11).
    @worker.rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        context.add_message(
            {
                "role": "system",
                "content": (
                    "A guest just stepped up to the screen. Open warmly in ONE short, "
                    "natural line — in their likely language — and invite them in."
                ),
            }
        )
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Guest connected")

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Guest disconnected")
        await worker.cancel()

    runner = WorkerRunner(handle_sigint=False)
    await runner.add_workers(worker)
    await runner.run()


# ── Entrypoint: the dev runner hands us a WebRTC connection (§6.1) ─────────────
async def bot(runner_args: RunnerArguments):
    """Discovered and called by `pipecat.runner.run.main()`."""
    match runner_args:
        case SmallWebRTCRunnerArguments():
            webrtc_connection: SmallWebRTCConnection = runner_args.webrtc_connection
            transport = SmallWebRTCTransport(
                webrtc_connection=webrtc_connection,
                params=TransportParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                    video_out_is_live=True,
                    # Lock to the venue screen early — portrait vs landscape changes
                    # face framing (§5, §21). Defaults to a portrait-ish kiosk frame.
                    video_out_width=int(os.getenv("VIDEO_OUT_WIDTH", "768")),
                    video_out_height=int(os.getenv("VIDEO_OUT_HEIGHT", "1024")),
                ),
            )
        case _:
            logger.error(f"Unsupported runner arguments type: {type(runner_args)}")
            return

    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
