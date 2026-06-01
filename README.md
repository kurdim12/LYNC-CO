# LIV — Lynk & Co Conversational Avatar

A live, on-screen brand host for a Lynk & Co activation: a guest speaks through a headset
and **Liv** replies in real time with an expressive, lip-synced video face — in **English
and Levantine Arabic**. Built on [Pipecat](https://github.com/pipecat-ai/pipecat).

> 📖 **`DOCUMENTATION.md` is the source of truth.** `CLAUDE.md` is the short brief.
> `BUILD_PLAN.md` is the phase plan. Start there.

```
mic → Deepgram STT → LLM (Liv persona + 08 KB) → ElevenLabs TTS → Simli face → display
```

## Quickstart
```bash
# 1) Environment (Python 3.11+)
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
# (or: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)

# 2) Keys
cp .env.example .env        # fill DEEPGRAM / OPENAI / ELEVENLABS / SIMLI keys

# 3) Verify the install matches the code (no keys/mic needed)
python smoke_test.py

# 4) Run — opens a local WebRTC server
python bot.py               # then open http://localhost:7860 and talk to Liv
```

## Requirements to actually talk to Liv
- API keys for Deepgram, an LLM (OpenAI default), ElevenLabs, and Simli — plus a Simli
  `SIMLI_FACE_ID` (created from the generated Liv image, Phase 1).
- A microphone (event: a noise-cancelled **headset**).
- For the event: an **RTX GPU** machine (NVIDIA Broadcast mic cleanup), good speakers,
  dedicated wired internet + 5G failover, UPS. See `DOCUMENTATION.md` §5.

## Status — Phase 0 (the spike)
| | |
|---|---|
| ✅ | API verified against **installed Pipecat 1.3.0** (not assumed from old docs). |
| ✅ | `bot.py` — full streaming pipeline, persona + KB, LLM A/B, expressive TTS, Simli, latency metrics. |
| ✅ | `smoke_test.py` green; `python bot.py` boots the local WebRTC server + test client. |
| ⏳ | Live gates (spoken lip-synced reply, Levantine judged, latency ≤~1.5s, barge-in) — run on the RTX machine with real keys + mic + Simli face. |

## Key design rules
- **Verify Pipecat against the installed version before editing `bot.py`** — its API drifts
  (we're on the 1.x universal-context API). Re-run `smoke_test.py` after any `pipecat-ai` bump.
- **Liv never invents specs/prices.** Her only car facts are in `knowledge/lynkco_08.md`;
  unknowns are handed off to a human. Real numbers require **brand sign-off** (§18, §21).
- **Levantine, not MSA**, for Arabic. Short, human, never robotic (§9).

## Layout
```
bot.py                     Pipecat spike (the pipeline)
smoke_test.py              API/wiring verification
prompts/liv_persona_v1.md  Liv's character (system prompt)
knowledge/lynkco_08.md     The only source of car facts (KB template; brand-approved values TBC)
requirements.txt  .env.example
DOCUMENTATION.md  CLAUDE.md  BUILD_PLAN.md
display/                   Next.js display + /operator — static export, Cloudflare Pages-ready
deploy/                    Bot container (Dockerfile) + Pipecat Cloud config
DEPLOY.md                  How to host the display (Cloudflare/Vercel) + the bot
```

## Hosting
The **display** (`display/`) is a static Next.js app → **Cloudflare Pages** (or Vercel). The
**bot** (`bot.py`) is a persistent WebRTC + ML server → **Pipecat Cloud / a VM / the venue PC**
(it can't run on serverless edge). Full manual deploy steps in **`DEPLOY.md`**.
