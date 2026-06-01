# Liv — Face Spec & Avatar Setup (Phase 1)

This unlocks the **talking face** — the single biggest upgrade from "voice demo" to "wow."
You generate one image of Liv, turn it into an avatar, set two env vars, and `bot_realtime.py`
becomes Liv-with-a-face (realtime voice **+** lip-synced video).

> ⚖️ **Brand/legal (DOCUMENTATION.md §18):** Liv must be an **original digital persona** — she
> must **not** resemble an identifiable real person. Generated faces are fine; do not use a
> photo of a real individual. Usage rights for this activation sit with the client.

---

## 1. The look (creative brief)
- **Who:** "Liv" — a Gen-Z, European-leaning digital brand host. Age read ~22–27.
- **Vibe:** Zara-editorial, neutral-premium, design-led. Cool but warm and approachable —
  confident, not corporate. Think a stylish gallery host, not a call-center avatar.
- **Styling:** minimal, modern, monochrome/neutral wardrobe (a clean tee, knit, or blazer in
  black/grey/cream). Tidy hair off the face. Natural, light makeup. No loud logos or patterns.

## 2. Technical requirements (so it works as an avatar)
A single-image avatar (Simli/HeyGen) lip-syncs best from a clean, front-on portrait:
- **Framing:** head-and-shoulders, centered, facing the camera straight on.
- **Expression:** relaxed, friendly-neutral; **mouth closed or barely open**; **eyes open**,
  looking into the lens.
- **Lighting:** soft, even studio light; no harsh shadows across the face.
- **Background:** plain, uncluttered (off-white / light grey / soft gradient).
- **Orientation:** **portrait** (vertical) to match a kiosk screen — e.g. 896×1152 or 1024×1280.
- **Quality:** photorealistic, sharp focus on the face, high resolution.
- **Avoid:** glasses/hats/hair covering the face, hands in frame, multiple people, extreme
  angles, exaggerated expression, busy backgrounds.

## 3. Ready-to-use image prompt
Paste into your image generator (Midjourney / DALL·E / Imagen / Flux, etc.):

> Photorealistic studio portrait of an original fictional young woman, early-to-mid 20s,
> European features, "Gen-Z editorial" energy — cool, confident, approachable. Head and
> shoulders, facing camera straight on, relaxed friendly-neutral expression, mouth closed,
> eyes open looking into the lens. Minimal modern styling, neutral monochrome top (black or
> cream), tidy hair away from the face, natural light makeup. Soft even studio lighting, no
> harsh shadows. Clean off-white seamless background. Vertical portrait, high resolution,
> sharp focus on the face. Premium fashion-brand campaign aesthetic.

**Negative prompt** (if your tool supports it):
> text, watermark, logo, multiple people, hands, extreme angle, side profile, exaggerated
> expression, open mouth, teeth, sunglasses, hat, hair over eyes, deformed features, blurry,
> resembling any real or famous person.

Generate a few; pick the cleanest, most neutral, most "screen-ready" one. Keep the source
file out of git (it's gitignored under `assets/face_raw/`).

---

## 4. Turn the image into an avatar + set env

### Option A — Simli (cheapest, already wired) ✅
1. Go to **app.simli.com** → sign up → **Create Face** → upload Liv's image → get the **Face ID**.
2. Copy your **API key** (Account/Settings).
3. Add to `.env`:
   ```
   SIMLI_API_KEY=your_simli_key
   SIMLI_FACE_ID=your_face_id
   # If Simli gives a Trinity (expressive) face, keep SIMLI_TRINITY=true and, if it shows a
   # "faceId/emotionId" pair, put that whole string in SIMLI_FACE_ID.
   ```
4. Run: `python bot_realtime.py` → open http://localhost:7860 → Liv now has a face. 🎭

### Option B — HeyGen (more photoreal, pricier)
HeyGen "Interactive/Photo Avatar" is more lifelike. Pipecat has `HeyGenVideoService`
(`pip install "pipecat-ai[heygen]"`). Tell me if you want this and I'll wire a HeyGen branch
(needs a HeyGen API key + avatar id).

---

## 5. What you'll have after this
- **Realtime voice** (natural, bilingual EN/Levantine) **+ a lip-synced video face** of Liv,
  from just your **OpenAI** key + a **Simli** account. No Deepgram, no ElevenLabs.
- That's the full "AI brand host" experience — the thing that actually wows people.

> Next upgrades after the face: a **signature cloned voice** (when an ElevenLabs key with
> text-to-speech permission is ready) and the **polished full-screen display** (`display/`).
