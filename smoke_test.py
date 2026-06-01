#
# LIV — API smoke test.
#
# DOCUMENTATION.md §20: "Pipecat import errors -> version drift." This script makes
# the doc's "verify against the installed version FIRST" rule runnable. It imports
# everything bot.py depends on, constructs every pipeline stage with dummy keys, and
# wires the full Pipeline + PipelineWorker — WITHOUT any network, mic, GPU, or real
# keys. Run it after install and after every `pipecat-ai` bump:
#
#     python smoke_test.py
#
# Green here means bot.py's imports/wiring match the installed Pipecat. It does NOT
# test live audio/latency/barge-in — those need the real headset + RTX machine.

import os
import warnings

# Dummy keys so constructors that read env don't blow up (nothing connects at init).
for _k in (
    "DEEPGRAM_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "SIMLI_API_KEY",
    "SIMLI_FACE_ID",
):
    os.environ.setdefault(_k, "smoke-test")

ok, fail = [], []


def check(label, fn):
    try:
        fn()
        ok.append(label)
    except Exception as e:  # noqa: BLE001 - we want to report, not raise
        fail.append(f"{label}: {type(e).__name__}: {e}")


def main():
    # 1) Imports resolve (the #1 drift symptom).
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.frames.frames import LLMRunFrame  # noqa: F401
    from pipecat.observers.loggers.metrics_log_observer import MetricsLogObserver
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.worker import PipelineParams, PipelineWorker
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import (
        LLMContextAggregatorPair,
        LLMUserAggregatorParams,
    )
    from pipecat.runner.types import SmallWebRTCRunnerArguments  # noqa: F401
    from pipecat.services.deepgram.stt import DeepgramSTTService
    from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
    from pipecat.services.openai.llm import OpenAILLMService
    from pipecat.services.simli.video import SimliVideoService
    from pipecat.transports.base_transport import TransportParams  # noqa: F401
    from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport  # noqa: F401
    from pipecat.workers.runner import WorkerRunner  # noqa: F401

    print("✓ all imports resolved")

    # 2) bot.py itself imports and exposes the runner entrypoint.
    import bot

    check("bot.py exposes async bot()/run_bot()", lambda: (bot.bot, bot.run_bot, bot.create_llm))
    check("load_system_prompt() reads persona + knowledge", lambda: _assert_prompt(bot))

    # 3) Each stage constructs with the canonical (non-deprecated) settings= API.
    #    Treat any DeprecationWarning as a failure so we keep bot.py on the clean path.
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)

        check(
            "Deepgram STT (nova-3 / multi)",
            lambda: DeepgramSTTService(
                api_key="x",
                settings=DeepgramSTTService.Settings(model="nova-3", language="multi"),
            ),
        )
        check("OpenAI LLM (gpt-4o)", lambda: bot.create_llm())
        check(
            "ElevenLabs TTS (flash v2.5, expressive)",
            lambda: ElevenLabsTTSService(
                api_key="x",
                settings=ElevenLabsTTSService.Settings(
                    voice="x", model="eleven_flash_v2_5", stability=0.4, style=0.6,
                    use_speaker_boost=True,
                ),
            ),
        )
        check(
            "Simli video (trinity)",
            lambda: SimliVideoService(api_key="x", face_id="x", is_trinity_avatar=True),
        )

    # 4) Context + aggregators + full pipeline + worker wire up.
    ctx = LLMContext(messages=[{"role": "system", "content": "hi"}])
    aggs = LLMContextAggregatorPair(
        ctx, user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer())
    )

    def build_pipeline():
        Pipeline(
            [
                OpenAILLMService(api_key="x", settings=OpenAILLMService.Settings(model="gpt-4o")),
            ]
        )

    check("Pipeline construction", build_pipeline)

    def build_worker():
        p = Pipeline([])
        PipelineWorker(
            p,
            params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
            observers=[MetricsLogObserver()],
            idle_timeout_secs=300,
        )

    check("PipelineWorker (+metrics, +observer, +idle)", build_worker)
    check("Aggregator pair user()/assistant()", lambda: (aggs.user(), aggs.assistant()))

    # ── report ──
    print()
    for x in ok:
        print(" ✓", x)
    if fail:
        print("\nFAILURES:")
        for x in fail:
            print(" ✗", x)
        raise SystemExit(1)
    print("\n✅ smoke test passed — bot.py matches installed Pipecat.")


def _assert_prompt(bot_module):
    s = bot_module.load_system_prompt()
    assert "Liv" in s and "Lynk & Co 08" in s, "system prompt missing persona/knowledge content"


if __name__ == "__main__":
    main()
