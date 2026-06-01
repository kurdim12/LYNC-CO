# CLAUDE.md — LIV (Lynk & Co Conversational Avatar)

**Read `DOCUMENTATION.md` first — it is the single source of truth.** This file is the
short brief and the hard rules; the full spec, architecture, stack rationale, and phase
plan live in `DOCUMENTATION.md`.

## What this is
**Liv** — a live, on-screen brand host for a Lynk & Co activation (Jordan, June 20 2026).
A guest talks to her through a headset; she replies in real time with an expressive,
lip-synced video face, in **English and Levantine Arabic**. The bar is **"real, not
robotic."**

Pipeline (one streaming, overlapping loop):
`mic → Deepgram STT → LLM (Liv persona + 08 KB) → ElevenLabs TTS → Simli face → display`

## Repo map
| Path | What |
|---|---|
| `bot.py` | The Pipecat spike — the whole pipeline (Phase 0). |
| `smoke_test.py` | Verifies bot.py's imports/wiring against the installed Pipecat. |
| `prompts/liv_persona_v1.md` | Liv's character (system prompt). Versioned. |
| `knowledge/lynkco_08.md` | The ONLY source of car facts. Concatenated into context. |
| `requirements.txt`, `.env.example` | Deps + keys. |
| `display/` | Next.js display + `/operator` dashboard — static export, Cloudflare Pages-ready. |
| `deploy/` | Bot container (`Dockerfile`) + Pipecat Cloud config. See `DEPLOY.md`. |
| `BUILD_PLAN.md` | Phase-by-phase prompts. |

## Hard rules (do not break)
1. **Verify Pipecat against the installed version before editing `bot.py`.** Pipecat's API
   drifts (we are on **1.3.0**, the 1.x universal-context API). After any `pipecat-ai`
   bump, run `python smoke_test.py` and fix imports before trusting `bot.py`. Don't paste
   imports from old docs/training — confirm them in the installed package.
2. **Never invent car specs, prices, or availability.** Liv uses only `knowledge/lynkco_08.md`.
   Unknown → she hands off to a human. `‹TBC›` fields stay handoffs until a human enters a
   **brand-approved** value (§18, §21).
3. **Levantine, not MSA**, for Arabic. Replies stay short (1–3 sentences) and human.
4. **Don't print secrets.** Keys live in `.env` (gitignored).
5. Re-run the eval harness (Phase 1) after any persona change; track pass-rate (§14).

## Environment / running
```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env       # fill keys
python smoke_test.py       # API sanity (no keys/mic needed)
python bot.py              # opens local WebRTC server -> http://localhost:7860
```
The event machine needs an **RTX GPU** (NVIDIA Broadcast mic cleanup) + headset; the live
voice/latency/barge-in tests only mean something on that hardware (§5, §13).

## Current status — Phase 0 (the spike)
- ✅ `bot.py` runnable against verified Pipecat 1.3.0; `smoke_test.py` green; server boots.
- ⏳ Live gates (spoken lip-synced reply, Arabic judged, per-stage latency ≤~1.5s, barge-in)
  require real API keys + mic + a Simli `face_id` — run on the RTX machine. See `BUILD_PLAN.md`.

## Git
- Work on the feature branch noted in `BUILD_PLAN.md` / task. Commit per phase, clear messages.
- Do not open PRs unless explicitly asked.
