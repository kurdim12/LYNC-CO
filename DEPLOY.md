# DEPLOY.md — hosting Liv

Liv is **two services**, and they live in different places:

```
┌─────────────────────────────┐         WebRTC          ┌──────────────────────────────┐
│  DISPLAY (Next.js, static)   │  ──────────────────────▶│  BOT (Pipecat, Python)        │
│  Cloudflare Pages / Vercel   │   POST {BOT}/api/offer  │  Pipecat Cloud / VM / venue PC │
│  the browser UI + operator   │ ◀────────────────────── │  STT·LLM·TTS·Simli, holds the  │
└─────────────────────────────┘     audio + video       │  live peer connection + ML     │
                                                          └──────────────────────────────┘
```

**Why the split:** the bot is a long-running WebRTC media server with in-process ML — it
**cannot** run on Cloudflare or Vercel (serverless/edge: no persistent peer connections,
no GPU). Those platforms host the **display** only. The bot needs a real, always-on host.

---

## 1. Display → Cloudflare Pages  ✅ (this is the Cloudflare-ready part)

Static Next.js export (`display/out`). Two ways to deploy — both manual:

**Wrangler (direct upload):**
```bash
cd display
npm install
NEXT_PUBLIC_BOT_URL="https://your-bot-host" npm run build   # NEXT_PUBLIC_* is baked in at build
npx wrangler@latest pages deploy out --project-name=liv-display
```

**Pages Git integration (dashboard):** connect the repo →
- **Root directory:** `display`
- **Build command:** `npm run build` · **Output dir:** `out`
- **Env vars:** `NEXT_PUBLIC_BOT_URL` (+ optional `NEXT_PUBLIC_SHOW_CAPTIONS`, `NEXT_PUBLIC_ATTRACT_HEADLINE`)

> Cloudflare Pages serves HTTPS by default — required for mic access / WebRTC.
> (Vercel works identically: import `display/`, framework Next.js, same env var.)

---

## 2. Bot → somewhere persistent (NOT Cloudflare)

Pick one:

### Option A — Container on a VM / Fly.io / Render / Cloud Run  (matches current code)
Uses the bot's built-in SmallWebRTC server.
```bash
docker build -f deploy/Dockerfile -t liv-bot .
docker run --env-file .env -p 7860:7860 liv-bot     # public host → set NEXT_PUBLIC_BOT_URL to it
```
- Point the display's `NEXT_PUBLIC_BOT_URL` at this host's public HTTPS URL.
- **TURN required:** WebRTC media is UDP/ICE; behind NAT you must supply a TURN server (via
  ICE config) or browsers won't connect. CORS is already open on the bot, so cross-origin is fine.

### Option B — Pipecat Cloud  (managed)
The bot's native managed home. Config: `deploy/pcc-deploy.toml`.
- Pipecat Cloud usually fronts bots with the **Daily** transport (no TURN to run yourself).
  To use it: add the `daily` extra + Daily creds, and handle `DailyRunnerArguments` in
  `bot.py` (small addition; keep the SmallWebRTC branch for local). Then point the display's
  transport at Daily (`@pipecat-ai/daily-transport`). Verify steps against current Pipecat Cloud docs.

### Option C — The venue RTX machine (event day, lowest latency)
Run `python bot.py` locally next to the screen + headset (the architecture in DOCUMENTATION.md
§3). Display can be the local prebuilt client or this Next.js app pointed at `http://localhost:7860`.
This is the **event** setup; Options A/B are for **remote/online demos**.

---

## 3. Before it can actually talk (all paths)
- **Secrets** on the bot host (never in the image): `DEEPGRAM_API_KEY`, `OPENAI_API_KEY`
  (or Anthropic/Gemini), `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID`, `SIMLI_API_KEY` +
  **`SIMLI_FACE_ID`**.
- **Simli `face_id`** must exist (Phase 1: generate the Liv image → create the face). Without
  it, the bot connects but has no face.
- **Brand-approved car facts** in `knowledge/lynkco_08.md` before any public/event use (§18).

## 4. What's verified vs. what you must do
- ✅ Display **builds + serves** as a static export (CF Pages-ready); `bot.py` + `smoke_test.py` green.
- ⏳ I can't deploy from this sandbox — no Cloudflare/Vercel/Pipecat Cloud creds here (the wired
  Cloudflare account currently lists 0 accounts). Run the steps above under your own accounts.
- ⏳ Full end-to-end (talking, lip-sync, latency, barge-in) needs the keys + Simli face + a mic.
