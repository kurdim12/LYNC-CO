"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  PipecatClientAudio,
  usePipecatClient,
  usePipecatClientMediaTrack,
  usePipecatClientTransportState,
} from "@pipecat-ai/client-react";
import { RTVIEvent, type TranscriptData } from "@pipecat-ai/client-js";
import { connectParams } from "@/lib/pipecatClient";
import { ATTRACT_HEADLINE, SHOW_CAPTIONS } from "@/lib/config";
import { useLivEvent } from "@/lib/events";

export function LivStage() {
  const client = usePipecatClient();
  const state = usePipecatClientTransportState();
  const livVideo = usePipecatClientMediaTrack("video", "bot");
  const videoRef = useRef<HTMLVideoElement>(null);
  const clearTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [caption, setCaption] = useState("");

  // Compare transport state as a plain string (the union may add states over versions).
  const s: string = state;
  const live = s === "connected" || s === "ready";
  const connecting = !live && s !== "disconnected" && s !== "error";

  // Attach Liv's video track to the <video> element.
  useEffect(() => {
    const el = videoRef.current;
    if (el && livVideo) el.srcObject = new MediaStream([livVideo]);
  }, [livVideo]);

  // Live captions of what Liv is saying.
  useLivEvent(
    RTVIEvent.BotTranscript,
    useCallback((data: TranscriptData) => {
      if (!SHOW_CAPTIONS) return;
      if (clearTimer.current) clearTimeout(clearTimer.current);
      setCaption(data.text);
    }, []),
  );
  useLivEvent(
    RTVIEvent.BotStoppedSpeaking,
    useCallback(() => {
      if (clearTimer.current) clearTimeout(clearTimer.current);
      clearTimer.current = setTimeout(() => setCaption(""), 3000);
    }, []),
  );

  const start = useCallback(async () => {
    setError(null);
    try {
      await client?.connect(connectParams);
    } catch (e) {
      setError(
        e instanceof Error
          ? `Couldn't reach Liv — is the bot running? (${e.message})`
          : "Couldn't reach Liv. Check the bot is running.",
      );
    }
  }, [client]);

  return (
    <main className="stage">
      <video ref={videoRef} className={`liv-video ${live ? "visible" : ""}`} autoPlay playsInline />
      <PipecatClientAudio />

      {!live && (
        <div className="attract">
          <div className="brand">{"LYNK & CO"}</div>
          <h1>{ATTRACT_HEADLINE}</h1>
          <p>Your host for the 08. Ask her anything — in English or العربية.</p>
          <button className="cta" onClick={start} disabled={connecting}>
            {connecting ? "Connecting…" : "Tap to talk"}
          </button>
          {error && <p className="error">{error}</p>}
        </div>
      )}

      {live && SHOW_CAPTIONS && caption && (
        <div className="captions">
          <span>{caption}</span>
        </div>
      )}

      {live && (
        <div className="live-badge">
          <span className="dot" /> Live
        </div>
      )}
    </main>
  );
}
