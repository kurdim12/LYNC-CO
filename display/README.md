# Liv — Display (Next.js → Cloudflare Pages)

Full-screen WebRTC view of Liv + an `/operator` dashboard. It's a **static** Next.js app
(no server runtime) that connects from the browser to the **bot** (`../bot.py`) over WebRTC.

> The bot is a separate service — it can't run on Cloudflare/Vercel (persistent WebRTC + ML).
> See `../DEPLOY.md` for the full picture.

## Routes
- `/` — the display: Liv's lip-synced face, attract screen, live captions.
- `/operator/` — start/stop, mute, language lock, new-guest reset, fallback, health/log.

## Local dev
```bash
cd display
npm install
cp .env.example .env.local          # set NEXT_PUBLIC_BOT_URL=http://localhost:7860
npm run dev                          # http://localhost:3000  (run ../bot.py too)
```

## Build (static export → ./out)
```bash
npm run build      # produces ./out (static assets)
npm run preview    # optional: serve ./out locally
```

## Deploy to Cloudflare Pages (manual)
`NEXT_PUBLIC_*` is baked in at **build time**, so set it before building (or in the
Cloudflare Pages build settings).

**Option A — Wrangler (direct upload):**
```bash
NEXT_PUBLIC_BOT_URL="https://your-bot-host" npm run build
npx wrangler@latest pages deploy out --project-name=liv-display
```

**Option B — Cloudflare Pages Git integration (dashboard):**
- Connect the repo, set **Root directory** = `display`.
- Build command: `npm run build` · Output directory: `out`.
- Add env var `NEXT_PUBLIC_BOT_URL` (and optionally `NEXT_PUBLIC_SHOW_CAPTIONS`,
  `NEXT_PUBLIC_ATTRACT_HEADLINE`).

## Config (`.env` / Pages env vars)
| Var | Default | Notes |
|---|---|---|
| `NEXT_PUBLIC_BOT_URL` | `http://localhost:7860` | Bot WebRTC host; browser POSTs the SDP offer to `{URL}/api/offer`. |
| `NEXT_PUBLIC_SHOW_CAPTIONS` | `true` | Live captions on the display. |
| `NEXT_PUBLIC_ATTRACT_HEADLINE` | `Meet Liv` | Idle-screen headline. |

## Notes
- Built with `@pipecat-ai/client-js` + `@pipecat-ai/client-react` (SmallWebRTC transport),
  verified against the installed package versions.
- The bot's offer endpoint already sends permissive CORS, so cross-origin works; for public
  WebRTC you still need the bot reachable + a TURN server (or use the Daily transport). See
  `../DEPLOY.md`.
- WebRTC needs HTTPS in production (Cloudflare Pages serves HTTPS by default).
