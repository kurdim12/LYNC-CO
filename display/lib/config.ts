// Build-time config (NEXT_PUBLIC_* is inlined at build). See .env.example.

export const BOT_URL = (process.env.NEXT_PUBLIC_BOT_URL || "http://localhost:7860").replace(/\/+$/, "");

// The bot's SmallWebRTC signaling endpoint (Pipecat dev runner serves POST /api/offer).
export const OFFER_ENDPOINT = `${BOT_URL}/api/offer`;

export const SHOW_CAPTIONS = (process.env.NEXT_PUBLIC_SHOW_CAPTIONS ?? "true") !== "false";

export const ATTRACT_HEADLINE = process.env.NEXT_PUBLIC_ATTRACT_HEADLINE || "Meet Liv";
