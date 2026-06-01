# Liv bot — container image for a generic host (VM / Fly.io / Render / Cloud Run …).
#
# This runs bot.py's built-in SmallWebRTC dev server (the same one as local), bound to all
# interfaces. It pairs with the Cloudflare Pages display, which connects to {PUBLIC_URL}/api/offer.
#
# NOTE: WebRTC media uses UDP + ICE. Behind NAT/most clouds you MUST provide a TURN server
# (set it via env / ICE config) or browsers won't connect. The managed alternative is the
# Daily transport (no TURN to run) — see ../DEPLOY.md.  Build context = repo root:
#     docker build -f deploy/Dockerfile -t liv-bot .

FROM python:3.11-slim

WORKDIR /app

# Build deps for aiortc / PyAV media stack.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App + Liv's brain (persona) and knowledge base.
COPY bot.py ./
COPY prompts ./prompts
COPY knowledge ./knowledge

ENV LOG_LEVEL=INFO
EXPOSE 7860

# Keys come from the runtime env (.env is NOT baked in). Pass them with `docker run --env-file`.
CMD ["python", "bot.py", "--host", "0.0.0.0", "--port", "7860"]
