# LIV — Lynk & Co Conversational Avatar
## Complete Build Documentation for Claude Code

**Version:** 1.0 · **Date:** June 1, 2026 · **Target event:** June 20, 2026
**Build owner:** Abdelrahman Elkurdi · **Client:** Maranasi Events (Lynk & Co Jordan)
**Test vehicle:** Lynk & Co 08

> This is the single source of truth. Read it top to bottom before writing code.
> Tooling here is chosen as best-in-class for the job, not by preference or license.
> Where the underlying API can drift between releases (notably Pipecat), this doc tells
> you to **verify against the installed version first** — do that, don't assume.

---

## 1. What we are building
A live, on-screen brand host — **Liv** — for a Lynk & Co activation. A guest speaks to
her naturally through a noise-cancelled headset; she answers in **real time** with a
**lip-synced, expressive video face** and natural delivery, in **English and Levantine
Arabic**. She carries the Lynk & Co personality (cool, design-led, anti-dealer) and the
*skills* of a great salesperson without the pushiness. She is the car's representative.

The experience must feel **real, not robotic**. That single bar drives every decision.

---

## 2. Success criteria
**Overall (event-ready):**
- Natural spoken conversation, EN + Levantine, with a believable lip-synced face.
- Perceived first response ≤ ~1.5s; barge-in (interrupt) works like a human.
- Never invents specs/prices; never breaks character; un-trollable on a public screen.
- Survives a venue network hiccup (fallback) and runs unattended-ish with an operator.

**Phase 0 (the spike) — the gate everything else waits behind:**
- `python bot.py` opens a local WebRTC server.
- Talking into the mic returns a spoken Liv reply with a visible lip-synced face.
- Arabic in → natural Levantine out (judged good, or we clone a voice).
- Per-stage latency logged; total perceived ≤ ~1.5s.
- Barge-in confirmed.

---

## 3. Architecture
One streaming loop, every stage feeding the next, all overlapping:

```
Headset mic
   │  (NVIDIA Broadcast removes floor noise → clean virtual mic)
   ▼
┌──────────────────────── Pipecat pipeline (Python, on the RTX machine) ───────────────┐
│  Transport.input (local WebRTC, VAD)                                                  │
│     → Deepgram STT (Levantine + EN, streaming, interim results)                       │
│     → LLM (Liv persona + 08 knowledge in context; streams tokens)                     │
│     → ElevenLabs TTS (branded voice; streams audio; starts on first sentence)         │
│     → Simli video (audio → real-time lip-synced face)                                 │
│  Transport.output (WebRTC video+audio)                                                │
└───────────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
Next.js full-screen DISPLAY  ◄── separate /operator dashboard (start/stop, mute, reset, fallback)
```

**Why streaming/overlap:** TTS begins on the LLM's first sentence while it's still
writing the rest; Simli renders as audio arrives. That overlap is what turns a
"type → wait → answer" bot into something that feels alive.

**Why a local WebRTC transport (not a cloud room):** the machine sits at the venue next
to the screen; keeping transport local cuts a network hop and a cloud dependency.

---

## 4. The stack (chosen best-in-class)

| Layer | Choice | Why this one | Considered & rejected |
|---|---|---|---|
| **Orchestration** | **Pipecat** | The leading open framework for real-time voice/video agents; total pipeline control, 60+ swappable services, native Simli/Deepgram/ElevenLabs stages, built-in barge-in & debugging. | LiveKit Agents (excellent, but optimized for multi-party cloud rooms we don't need); all-in-one avatar platforms (rejected earlier — cost + no control over Arabic). |
| **STT** | **Deepgram Nova-3** | Best measured Levantine word-error-rate with ~400ms response; handles dialect + code-switch. | Whisper (fails on Arabic); ElevenLabs STT (too slow for real-time); Speechmatics (fast but lower accuracy). |
| **LLM (brain)** | **GPT-4o** default; evaluate **Gemini Flash** & **Claude** in the spike | Strong Arabic, fast streaming, reliable persona-following. Pick the winner on Arabic quality + latency. | — (this is a measured choice, made in Phase 0). |
| **TTS** | **ElevenLabs Flash v2.5 (multilingual)** | Best multilingual naturalness at low latency; Levantine voices + voice cloning for a branded voice. | Cartesia (lower latency but weaker Arabic) — keep as fallback. |
| **Face** | **Simli (Trinity)** | Custom face **from a single image**, sub-300ms, Pipecat-native, cents/min. Lets us use our generated Liv. | Tavus / Anam / HeyGen (higher fidelity but pricier/heavier, some bundle the pipeline). **If Simli realism isn't enough in the spike, evaluate Tavus or Anam as a drop-in face stage.** |
| **Mic cleanup** | **NVIDIA Broadcast** | Best-in-class real-time mic noise removal; exposes a clean virtual mic. Needs an RTX GPU. | Krisp (good alternative if no RTX). |
| **Display** | **Next.js** | Full-screen WebRTC client + operator route. |  |

**Latitude:** if the spike reveals a better option for a stage, swap it — Pipecat makes
each stage independent. Don't anchor on this table over real test results.

---

## 5. Environment & setup
**Hardware (event):**
- RTX laptop / mini-PC (NVIDIA Broadcast requires a GeForce/RTX GPU).
- Client-provided screen (lock resolution + orientation early — affects face framing).
- Headset mic; quality speakers.
- **Dedicated wired internet + a 5G failover.** This is the single biggest live-event risk.
- UPS / battery buffer so a power flicker doesn't reboot mid-conversation.

**Software:**
```bash
python -m venv .venv && source .venv/bin/activate   # or use uv
pip install "pipecat-ai[deepgram,openai,elevenlabs,simli,silero,webrtc]" python-dotenv loguru
cp .env.example .env   # fill keys
```

**Environment variables (`.env`):**
```
DEEPGRAM_API_KEY=        # STT
OPENAI_API_KEY=          # LLM (default)
GEMINI_API_KEY=          # optional, for A/B
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=     # chosen or cloned voice
SIMLI_API_KEY=
SIMLI_FACE_ID=           # created from the generated Liv image
```

**First, always:** `pip show pipecat-ai` to get the version, then confirm the import
paths and the context-aggregator API against the installed package or docs.pipecat.ai.
The `pipecat` CLI can scaffold a known-good baseline: `uv tool install pipecat-ai-cli`
then `pipecat init`. Build Liv on top of a baseline you've confirmed runs.

> **Build note (this repo):** the installed version is **Pipecat 1.3.0** (the 1.x line).
> The 1.x API differs from older examples — see §20 and `bot.py`'s header for the verified
> import/wiring facts. After any `pipecat-ai` bump, run `python smoke_test.py`.

---

## 6. Component reference

### 6.1 Transport + VAD (local WebRTC)
- Use Pipecat's local WebRTC transport so the display connects on the same machine/LAN.
- Attach a Silero VAD analyzer for voice-activity detection.
- Barge-in: interruptions are enabled (in Pipecat 1.x they are on by default).

### 6.2 STT — Deepgram Nova-3 (Arabic + EN)
- Configure for Levantine + English / code-switching (Nova-3 multilingual). Confirm the
  exact `model` / `language` params for your Deepgram SDK + Pipecat version.
- Use interim results + endpointing so turn-taking feels snappy, not chopped.
- In the spike, sanity-check it transcribes Jordanian colloquial, not just MSA.

### 6.3 LLM — the brain
- System message = `prompts/liv_persona_v1.md` **+** `knowledge/lynkco_08.md`, concatenated.
- Keep generation short (this is speech): cap tokens, instruct 1–3 sentences.
- Stream tokens so TTS can start on sentence 1.
- A/B GPT-4o vs Gemini Flash vs Claude on Arabic naturalness + latency; lock the winner.

### 6.4 TTS — ElevenLabs Flash
- Use the low-latency multilingual model; put the chosen/cloned `voice_id` in `.env`.
- Tune stability/style so Liv sounds *expressive and into it*, not flat.
- Decide in the spike: stock Levantine voice vs a custom clone (clone if naturalness is off).

### 6.5 Face — Simli (Trinity)
- `SimliVideoService(api_key=..., face_id=..., is_trinity_avatar=True)`.
- Pipeline position is critical: Simli comes **after** TTS so it lip-syncs the audio.
- Set idle/session timeouts to release minutes (cost control).

### 6.6 Pipeline assembly (shape)
```
Pipeline([
    transport.input(),
    stt,
    user_context_aggregator,
    llm,
    tts,
    simli,              # audio → talking face
    transport.output(),
    assistant_context_aggregator,
])
```
Run via the 1.x worker/runner with metrics enabled. Verify aggregator class names against
the installed version (in 1.3.0: `LLMContext` + `LLMContextAggregatorPair`, with the VAD
analyzer passed via `LLMUserAggregatorParams`).

---

## 7. Persona & knowledge
- **`prompts/liv_persona_v1.md`** — Liv's system prompt (identity, goal, tone, language
  rules, sales arc, guardrails, few-shot EN + Levantine examples). This is the brain's
  character. Version it; improve it through the eval harness (§14).
- **`knowledge/lynkco_08.md`** — the only source of car facts. Injected into context.
  **Populate from official Lynk & Co material + the client brief. Never guess numbers.**
  Anything not in this file → Liv hands off to a human.
- One car = a small, fixed domain, so **no vector DB / RAG needed** — the KB fits in context.

---

## 8. Bilingual handling
- Reply in the guest's language; **Levantine, not MSA**, for Arabic.
- On code-switch, match the dominant language; switch naturally like a bilingual person.
- Never switch language mid-reply unless the guest did.
- Test explicitly: pure Arabic, pure English, and mixed ("hi kifak, what's the range?").

---

## 9. Realism requirements ("not robotic")
Three layers, all required:
1. **Voice** — expressive TTS settings; contractions; real Levantine particles
   ("تمام", "يلا"); never the flat "I am happy to assist you" cadence.
2. **Timing** — low latency + barge-in + a natural micro-acknowledgment instead of dead
   air while the brain forms a reply. Dead air and over-politeness scream "AI."
3. **Face** — Simli expressive model: blinks, micro-expressions, head/idle motion. No
   frozen stare.

---

## 10. Guardrails & safety
Encode in the system prompt **and** verify with tests:
- **No hallucinated specs/prices** — unknown → "let me grab a teammate with the exact number."
- **Anti-troll** — refuse-and-redirect with charm; never go political/off-brand/silly;
  never break character. People *will* try to make her say something dumb on camera.
- **Bilingual + short + human** as above.
- **Operator override** — a kill / redirect / reset control always available (§11).
- **Brand** — access/membership/community over ownership; never pushy; never trash rivals.

---

## 11. Front-end
**Display app (Next.js, full-screen):**
- Connects to the bot's local WebRTC; shows Liv's video + audio.
- Attract/idle loop when no one is talking (invites people over).
- Optional live captions.

**Operator dashboard (`/operator`, separate route):**
- Start/stop session, mute, **language lock**, **reset conversation** (new guest),
  **switch to fallback**, and a latency/health readout.

---

## 12. Fallback & reliability
- **Connectivity/API drop:** auto-engage a degraded mode — a pre-rendered Liv loop +
  a few scripted lines — so the screen never goes dead.
- **Watchdog:** auto-restart a crashed session; idle timeout releases Simli minutes.
- **Echo:** Liv's speaker output can leak into the mic and false-trigger her. The headset
  largely solves it (mic at the mouth); confirm echo handling in the spike.

---

## 13. Latency

| Stage | Budget |
|---|---|
| STT (Deepgram, streaming) | ~400 ms |
| LLM first token | ~300–500 ms |
| TTS first audio (ElevenLabs Flash) | ~150–250 ms |
| Simli render | ~300 ms |
| **Perceived first response (overlapped)** | **~1–1.5 s** |

Log per-stage timing from day one. If you're over budget, the usual culprits are
non-streaming LLM calls or waiting for full sentences before TTS.

> In this repo, `bot.py` enables Pipecat metrics and attaches a `MetricsLogObserver`
> (per-stage TTFB) plus the built-in `UserBotLatencyObserver` (perceived latency).

---

## 14. Testing & eval harness
Build a small harness that runs Liv's prompt against ~15 cases and reports pass/fail:
- Greeting, a benefit question, a price objection, an off-topic question, a **troll
  attempt**, a spec question with a missing number (must hand off), pure Arabic, pure
  English, a code-switched line.
- Assert: stays in character, right language, ≤3 sentences, no invented numbers,
  deflects the troll. Re-run after every prompt change; track a pass-rate.

---

## 15. Cost model (event-day, usage-based)
- Simli (per minute), Deepgram (per minute), LLM (per token), ElevenLabs (per character/min).
- Pipecat is free; you pay the machine it runs on.
- Estimate from expected talk-minutes, set a cap, and confirm before the event. This is
  the usage cost folded into the client proposal.

---

## 16. Build plan — phases & Claude Code prompts
Work in order. Each phase ends with a working, committed checkpoint. (Mirrored in `BUILD_PLAN.md`.)

**Phase 0 — Spike (Jun 1–4) — START HERE.**
> "Read this doc. Confirm the installed Pipecat version and the real import/context APIs,
> and build a runnable `bot.py`: local WebRTC transport + VAD, system context from
> `prompts/liv_persona_v1.md` + `knowledge/lynkco_08.md`, pipeline STT→LLM→TTS→Simli with
> barge-in. Get a spoken, lip-synced reply from my mic, log per-stage latency, and help me
> test an Arabic exchange and judge the Levantine voice."

**Phase 1 — Persona + face (Jun 5–9).**
> "Generate the Liv face image to spec (original Gen-Z European, Zara-editorial, neutral
> premium — not a real person), create the Simli face, set SIMLI_FACE_ID. Build the eval
> harness (§14) and tune `liv_persona_v1.md` to pass."

**Phase 2 — Display + operator (Jun 10–14).**
> "Create `display/` (Next.js): full-screen WebRTC view of Liv with an attract loop and
> optional captions, plus a `/operator` route (start/stop, mute, language lock, reset,
> fallback, health). Clean Lynk & Co look."

**Phase 3 — Harden (Jun 15–17).**
> "Add fallback mode, a watchdog + idle timeout, echo/barge-in stress tests through the
> headset, and metrics logging (conversation count, length, top questions)."

**Phase 4 — On-site (Jun 18–20).**
> Rehearse on the real machine/screen/headset/network with 5G failover; dry-run with
> strangers; lock attract copy; operator on the dashboard on event day.

---

## 17. On-site operations
- **Brand ambassador** runs the line: hands the headset, guides first-timers, taps "new
  guest" to reset Liv between people. **Disposable headset covers** (hygiene).
- One headset = one conversation at a time; if the queue grows, add a second station
  (extra machine + usage cost).
- Optional: record the conversation and hand the guest a clip via QR — amplifies reach
  and ties Liv to the selfie-wall activation as one "AI experience zone."

---

## 18. Brand, legal & data (must be settled before go-live)
- **Brand sign-off:** Lynk & Co / Jordan distributor approves Liv's persona and script.
  No price/availability/promise claims go live without approval; this protects you.
- **Face rights:** the generated Liv face is original and must not resemble an
  identifiable real person; usage rights for this activation sit with the client.
- **Consent & data:** if audio is recorded or contacts captured, there's an on-site
  consent notice; leads/conversation data ownership is agreed in writing.

---

## 19. Repo layout & conventions
```
liv-avatar/
  DOCUMENTATION.md        ← this file (source of truth)
  CLAUDE.md               ← short brief; points here
  BUILD_PLAN.md           ← the phase prompts above
  bot.py                  ← Pipecat spike (verify imports vs installed version)
  smoke_test.py           ← verifies bot.py against the installed Pipecat
  .env.example
  requirements.txt
  prompts/liv_persona_v1.md
  knowledge/lynkco_08.md
  display/                ← Next.js app (Phase 2)
```
- `uv` (or venv) for envs. Secrets in `.env` (gitignored); never print keys.
- `loguru` logging; `LOG_LEVEL=DEBUG` for verbose frames.
- Commit per phase with clear messages.

---

## 20. Troubleshooting / pitfalls
- **Pipecat import errors** → version drift. `pip show pipecat-ai`, check the package's
  actual module paths; don't trust scaffolded imports. Scaffold a baseline with the CLI.
  *(In 1.3.0: services live under `pipecat.services.<name>.<stt|llm|tts|video>`; context is
  `pipecat.processors.aggregators.llm_context.LLMContext` + `…llm_response_universal.
  LLMContextAggregatorPair`; the VAD analyzer is passed via `LLMUserAggregatorParams`, not
  TransportParams; use `PipelineWorker` + `WorkerRunner` (`PipelineTask` is deprecated);
  configure services with `settings=Service.Settings(...)`.)*
- **Arabic transcribed as gibberish** → wrong STT language/model; confirm Nova-3 Arabic
  config and that you're sending it Levantine, not expecting MSA. (`DEEPGRAM_LANGUAGE=multi`
  for code-switch; fall back to `ar` if needed.)
- **Flat/robotic voice** → ElevenLabs stability too high; loosen style; consider a clone.
- **Lip-sync looks off** → Simli must be *after* TTS; check audio sample rate/format it expects.
- **Dead air before replies** → LLM not streaming, or TTS waiting for full output; stream both.
- **She false-triggers herself** → speaker→mic echo; rely on headset mic placement; confirm.
- **Latency creeping up** → measure per stage; the LLM or non-streaming TTS is usually it.

---

## 21. Open items (need input/assets)
- [ ] Generate the Liv face image → create Simli `face_id`. (Spec in §16 / Phase 1.)
- [ ] Populate `knowledge/lynkco_08.md` with real 08 specs + Jordan pricing (client-approved).
- [ ] Confirm screen resolution/orientation (portrait vs landscape).
- [ ] API accounts + a usage cap.
- [ ] Confirm RTX machine + headset + dedicated internet/5G failover.
- [ ] Brand sign-off on persona/script; consent + data-ownership agreed.
