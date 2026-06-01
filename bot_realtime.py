#
# LIV — REALTIME mode (the simplest path that works).
#
# One service does everything: OpenAI's Realtime speech-to-speech model LISTENS, THINKS,
# and SPEAKS in a single connection. No Deepgram, no ElevenLabs — so none of the things
# that kept breaking. It needs ONLY your OPENAI_API_KEY (the one that already works).
#
#   python bot_realtime.py      →  open http://localhost:7860
#
# Verified against installed Pipecat 1.3.0 (OpenAIRealtimeLLMService, gpt-realtime-2).
# When you later want a custom Levantine voice / lip-synced face, use bot.py (cascade).

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from pipecat.frames.frames import LLMRunFrame
from pipecat.observers.loggers.transcription_log_observer import TranscriptionLogObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.runner.types import RunnerArguments, SmallWebRTCRunnerArguments
from pipecat.services.openai.realtime.events import (
    AudioConfiguration,
    AudioInput,
    AudioOutput,
    SessionProperties,
    TurnDetection,
)
from pipecat.services.openai.realtime.llm import OpenAIRealtimeLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.workers.runner import WorkerRunner

load_dotenv(override=True)
logger.remove()
logger.add(sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"))

ROOT = Path(__file__).resolve().parent


def load_system_prompt() -> str:
    """Liv's persona + the 08 knowledge base, concatenated into the realtime instructions."""
    persona = (ROOT / "prompts" / "liv_persona_v1.md").read_text(encoding="utf-8").strip()
    knowledge = (ROOT / "knowledge" / "lynkco_08.md").read_text(encoding="utf-8").strip()
    return (
        f"{persona}\n\n"
        "=== CAR FACTS (your ONLY source of specs/prices — never go beyond this) ===\n\n"
        f"{knowledge}"
    )


async def run_bot(transport: BaseTransport):
    logger.info("Starting Liv (REALTIME / OpenAI speech-to-speech) …")
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("✗ OPENAI_API_KEY is missing in .env — it's the ONLY key this mode needs. Add it and reconnect.")
        return

    voice = os.getenv("REALTIME_VOICE", "marin")  # marin/cedar = most natural; also coral, sage, alloy, verse…
    logger.info(f"Realtime voice: {voice}")

    # One service: audio in → (STT+LLM+TTS internally) → audio out. Persona goes in instructions;
    # turn-taking is handled server-side (server_vad), so no local STT/VAD/TTS needed.
    llm = OpenAIRealtimeLLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        settings=OpenAIRealtimeLLMService.Settings(
            session_properties=SessionProperties(
                instructions=load_system_prompt(),
                audio=AudioConfiguration(
                    input=AudioInput(turn_detection=TurnDetection(type="server_vad")),
                    output=AudioOutput(voice=voice),
                ),
            ),
        ),
    )

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(context)

    # Optional FACE — Simli lip-syncs the realtime audio into a talking video of Liv.
    # Set SIMLI_API_KEY + SIMLI_FACE_ID (see assets/liv_face_spec.md) to turn it on.
    video = None
    if (
        os.getenv("SIMLI_API_KEY")
        and os.getenv("SIMLI_FACE_ID")
        and os.getenv("DISABLE_FACE", "").lower() not in ("1", "true", "yes")
    ):
        from pipecat.services.simli.video import SimliVideoService

        video = SimliVideoService(
            api_key=os.getenv("SIMLI_API_KEY"),
            face_id=os.getenv("SIMLI_FACE_ID"),
            is_trinity_avatar=os.getenv("SIMLI_TRINITY", "true").lower() in ("1", "true", "yes"),
        )
        logger.info("Simli FACE enabled — Liv will be a talking video.")
    else:
        logger.info("Audio-only (no face). Add SIMLI_API_KEY + SIMLI_FACE_ID for a talking face — see assets/liv_face_spec.md.")

    stages = [transport.input(), user_aggregator, llm]
    if video is not None:
        stages.append(video)  # realtime audio -> lip-synced face (must be after the LLM)
    stages += [transport.output(), assistant_aggregator]
    pipeline = Pipeline(stages)

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        observers=[TranscriptionLogObserver()],
    )

    @worker.rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        context.add_message(
            {"role": "user", "content": "A guest just stepped up. Greet them warmly in ONE short line and invite them in."}
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


async def bot(runner_args: RunnerArguments):
    # Turn on live video output only when a Simli face is configured.
    face_on = bool(os.getenv("SIMLI_API_KEY") and os.getenv("SIMLI_FACE_ID")) and os.getenv(
        "DISABLE_FACE", ""
    ).lower() not in ("1", "true", "yes")
    params = TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        video_out_is_live=face_on,
        video_out_width=int(os.getenv("VIDEO_OUT_WIDTH", "768")) if face_on else 1024,
        video_out_height=int(os.getenv("VIDEO_OUT_HEIGHT", "1024")) if face_on else 768,
    )

    match runner_args:
        case SmallWebRTCRunnerArguments():
            webrtc_connection: SmallWebRTCConnection = runner_args.webrtc_connection
            transport = SmallWebRTCTransport(webrtc_connection=webrtc_connection, params=params)
        case _:
            logger.error(f"Unsupported runner arguments type: {type(runner_args)}")
            return

    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
