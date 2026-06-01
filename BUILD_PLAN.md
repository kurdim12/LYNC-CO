# BUILD_PLAN.md — LIV phases

Work in order. Each phase ends with a working, committed checkpoint. Full detail in
`DOCUMENTATION.md` §16. Target event: **June 20, 2026**.

---

## Phase 0 — Spike (Jun 1–4) — ✅ scaffolded, ⏳ live-gated
**Prompt:** "Read this doc. Confirm the installed Pipecat version and the real import/context
APIs, and build a runnable `bot.py`: local WebRTC transport + VAD, system context from
`prompts/liv_persona_v1.md` + `knowledge/lynkco_08.md`, pipeline STT→LLM→TTS→Simli with
barge-in. Get a spoken, lip-synced reply from my mic, log per-stage latency, and help me
test an Arabic exchange and judge the Levantine voice."

**Done in this repo (cloud — no mic/GPU/keys):**
- [x] Verified API against **installed Pipecat 1.3.0** (not assumed): 1.x universal
      `LLMContext`/`LLMContextAggregatorPair`; VAD via `LLMUserAggregatorParams`;
      `settings=Service.Settings(...)`; `PipelineWorker` + `WorkerRunner`; interruptions on
      by default.
- [x] `bot.py` — full pipeline, persona+KB context, LLM A/B (OpenAI/Anthropic/Google),
      Deepgram Levantine+EN, ElevenLabs Flash v2.5 expressive, Simli Trinity, metrics +
      latency observers, idle timeout, greeting kickoff.
- [x] `smoke_test.py` green; `python bot.py` boots the local WebRTC server + test client.

**Gates to clear on the RTX machine (need keys + headset + Simli `face_id`):**
- [ ] Talk into the mic → spoken Liv reply with a visible lip-synced face.
- [ ] Arabic in → natural Levantine out (judge; clone the voice if it's off).
- [ ] Per-stage latency logged; total perceived ≤ ~1.5s.
- [ ] Barge-in (interrupt) confirmed through the headset.

---

## Phase 1 — Persona + face (Jun 5–9)
**Prompt:** "Generate the Liv face image to spec (original Gen-Z European, Zara-editorial,
neutral premium — not a real person), create the Simli face, set `SIMLI_FACE_ID`. Build the
eval harness (§14) and tune `liv_persona_v1.md` to pass."
- [ ] Generate Liv face → create Simli `face_id` (§21).
- [ ] Eval harness: ~15 cases (greeting, benefit, price objection, off-topic, troll,
      missing-spec handoff, pure AR, pure EN, code-switch). Assert: in character, right
      language, ≤3 sentences, no invented numbers, deflects troll. Track pass-rate.
- [ ] Tune persona to pass; re-run after every change.

## Phase 2 — Display + operator (Jun 10–14)
**Prompt:** "Create `display/` (Next.js): full-screen WebRTC view of Liv with an attract
loop and optional captions, plus a `/operator` route (start/stop, mute, language lock,
reset, fallback, health). Clean Lynk & Co look."

## Phase 3 — Harden (Jun 15–17)
**Prompt:** "Add fallback mode, a watchdog + idle timeout, echo/barge-in stress tests
through the headset, and metrics logging (conversation count, length, top questions)."

## Phase 4 — On-site (Jun 18–20)
Rehearse on the real machine/screen/headset/network with 5G failover; dry-run with
strangers; lock attract copy; operator on the dashboard on event day.

---

## Open items blocking go-live (DOCUMENTATION.md §21)
- [ ] Generate Liv face → Simli `face_id`.
- [ ] Populate `knowledge/lynkco_08.md` with real, **brand-approved** 08 specs + Jordan pricing.
- [ ] Confirm screen resolution/orientation (portrait vs landscape).
- [ ] API accounts + a usage cap.
- [ ] Confirm RTX machine + headset + dedicated internet/5G failover.
- [ ] Brand sign-off on persona/script; consent + data-ownership agreed.
