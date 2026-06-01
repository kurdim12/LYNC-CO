# Running Liv locally (and pushing to GitHub)

Liv is **two programs**: the **bot** (Python, `bot.py`) and the **display** (Next.js,
`display/`). Run the bot first; the display connects to it.

## Prerequisites
- **Python 3.11+**, **Node 18+**, **git**
- To actually see/hear Liv: API keys + a **Simli `face_id`** (see "Why nothing shows" below)

---

## 1. Get the code onto your machine
```bash
git clone https://github.com/kurdim12/LYNC-CO.git
cd LYNC-CO
git checkout claude/gallant-fermat-ZyYUZ
```

## 2. Run the bot  (terminal 1)
```bash
# from the repo root
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt                        # first time only (a few minutes)

cp .env.example .env                                   # then edit .env and add your keys
python smoke_test.py                                   # optional sanity check (no keys needed)
python bot.py                                          # → serves http://localhost:7860
```

## 3a. Quickest way to see it: the bot's built-in client
Open **http://localhost:7860** in your browser and click connect. This is the simplest
local test — no display app needed.

## 3b. Or run the full display  (terminal 2, leave the bot running)
```bash
cd LYNC-CO/display
npm install                                            # first time only
cp .env.example .env.local                             # NEXT_PUBLIC_BOT_URL=http://localhost:7860
npm run dev                                            # → http://localhost:3000
```
Open **http://localhost:3000** (display) or **http://localhost:3000/operator/** (dashboard).

---

## 4. Push changes to GitHub
The branch is already on GitHub. After editing:
```bash
git add -A
git commit -m "your message"
git push origin claude/gallant-fermat-ZyYUZ
```
(To put it on `main`, open a Pull Request on GitHub from this branch, or merge it.)

---

## Why "nothing" shows (and how to fix it)
The display is only a screen — it needs a reachable **bot** and Liv needs assets:

| Symptom | Cause | Fix |
|---|---|---|
| Hosted page is blank | Cloudflare Pages **Root directory** not set to `display` | Set root dir `display`, build `npm run build`, output `out` |
| "Tap to talk" does nothing on the hosted site | `NEXT_PUBLIC_BOT_URL` still `localhost` (a public HTTPS page can't call your localhost) | Host the bot somewhere public and set `NEXT_PUBLIC_BOT_URL` to its URL, then rebuild |
| Connects locally but **no face / no voice** | No API keys and/or no `SIMLI_FACE_ID` | Fill `.env`; create the Simli face (Phase 1) and set `SIMLI_FACE_ID` |
| `python bot.py` errors on connect | Missing/invalid keys | Check `.env` (`DEEPGRAM_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID`, `SIMLI_API_KEY` + `SIMLI_FACE_ID`) |

> Hosting the bot is **not** a Cloudflare/Vercel thing — it's a persistent WebRTC + ML
> server. See **`DEPLOY.md`** for where the bot can live (Pipecat Cloud / a VM / the venue PC).
