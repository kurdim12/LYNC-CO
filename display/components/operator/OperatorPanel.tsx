"use client";

import { useCallback, useEffect, useState } from "react";
import {
  usePipecatClient,
  usePipecatClientMicControl,
  usePipecatClientTransportState,
} from "@pipecat-ai/client-react";
import { RTVIEvent } from "@pipecat-ai/client-js";
import { connectParams } from "@/lib/pipecatClient";
import { BOT_URL } from "@/lib/config";
import { useLivEvent } from "@/lib/events";

type Lang = "auto" | "en" | "ar";

export function OperatorPanel() {
  const client = usePipecatClient();
  const state = usePipecatClientTransportState();
  const { enableMic, isMicEnabled } = usePipecatClientMicControl();

  const [lang, setLang] = useState<Lang>("auto");
  const [fallback, setFallback] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [since, setSince] = useState<number | null>(null);
  const [, tick] = useState(0); // re-render for the uptime clock

  const s: string = state;
  const live = s === "connected" || s === "ready";

  const push = useCallback(
    (m: string) => setLog((l) => [`${new Date().toLocaleTimeString()}  ${m}`, ...l].slice(0, 60)),
    [],
  );

  useLivEvent(RTVIEvent.Connected, useCallback(() => { setSince(Date.now()); push("connected"); }, [push]));
  useLivEvent(RTVIEvent.Disconnected, useCallback(() => { setSince(null); push("disconnected"); }, [push]));
  useLivEvent(RTVIEvent.BotReady, useCallback(() => push("bot ready"), [push]));

  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const start = useCallback(async () => {
    try { await client?.connect(connectParams); }
    catch (e) { push(`connect failed: ${(e as Error).message}`); }
  }, [client, push]);

  const stop = useCallback(async () => {
    try { await client?.disconnect(); } catch { /* ignore */ }
  }, [client]);

  const reset = useCallback(async () => {
    push("reset — new guest");
    try { await client?.disconnect(); } catch { /* ignore */ }
    await new Promise((r) => setTimeout(r, 400));
    await start();
  }, [client, start, push]);

  // Language lock + fallback are sent to the bot as client messages. They need a
  // matching on_client_message handler on the bot (Phase 3) — until then they no-op
  // server-side. The UI state still reflects the operator's intent.
  const lockLanguage = useCallback((l: Lang) => {
    setLang(l);
    try { client?.sendClientMessage("set-language", { language: l }); push(`language → ${l}`); }
    catch { push("language: bot handler not wired yet"); }
  }, [client, push]);

  const toggleFallback = useCallback(() => {
    const next = !fallback;
    setFallback(next);
    try { client?.sendClientMessage("set-fallback", { enabled: next }); push(`fallback → ${next ? "on" : "off"}`); }
    catch { push("fallback: bot handler not wired yet"); }
  }, [client, fallback, push]);

  const uptime = since ? Math.max(0, Math.floor((Date.now() - since) / 1000)) : 0;
  const mmss = `${String(Math.floor(uptime / 60)).padStart(2, "0")}:${String(uptime % 60).padStart(2, "0")}`;

  return (
    <div className="operator">
      <div className="op-head">
        <div>
          <div className="kicker">{"LYNK & CO · LIV"}</div>
          <h1>Operator</h1>
        </div>
        <span className={`pill ${live ? "live" : "off"}`}>
          <span className="dot" /> {live ? "Live" : s}
        </span>
      </div>

      <div className="op-grid">
        {/* Session */}
        <section className="card">
          <h2>Session</h2>
          <div className="btn-row">
            <button className="btn primary" onClick={start} disabled={live}>Start</button>
            <button className="btn danger" onClick={stop} disabled={!live}>Stop</button>
            <button className="btn" onClick={reset}>New guest</button>
          </div>
          <p className="hint">“New guest” resets the conversation between people.</p>
        </section>

        {/* Mic */}
        <section className="card">
          <h2>Microphone</h2>
          <div className="btn-row">
            <button
              className={`btn ${isMicEnabled ? "" : "active"}`}
              onClick={() => enableMic(!isMicEnabled)}
            >
              {isMicEnabled ? "Mute mic" : "Unmute mic"}
            </button>
          </div>
          <p className="hint">Mic is {isMicEnabled ? "open" : "muted"}.</p>
        </section>

        {/* Language lock */}
        <section className="card">
          <h2>Language lock</h2>
          <div className="seg">
            {(["auto", "en", "ar"] as Lang[]).map((l) => (
              <button key={l} className={lang === l ? "on" : ""} onClick={() => lockLanguage(l)}>
                {l === "auto" ? "Auto" : l.toUpperCase()}
              </button>
            ))}
          </div>
          <p className="hint">Force Liv’s reply language (or Auto / code-switch).</p>
        </section>

        {/* Fallback */}
        <section className="card">
          <h2>Fallback</h2>
          <div className="btn-row">
            <button className={`btn ${fallback ? "active" : ""}`} onClick={toggleFallback}>
              {fallback ? "Fallback ON" : "Engage fallback"}
            </button>
          </div>
          <p className="hint">Degraded mode (pre-rendered loop) if the network/API drops.</p>
        </section>

        {/* Health */}
        <section className="card">
          <h2>Health</h2>
          <div className="status-row"><span className="label">State</span><span className="value">{s}</span></div>
          <div className="status-row"><span className="label">Uptime</span><span className="value">{live ? mmss : "—"}</span></div>
          <div className="status-row"><span className="label">Bot</span><span className="value" style={{ fontSize: "0.8rem" }}>{BOT_URL}</span></div>
        </section>

        {/* Activity log */}
        <section className="card" style={{ gridColumn: "1 / -1" }}>
          <h2>Activity</h2>
          <div className="log">
            {log.length === 0 ? <div>— no events yet —</div> : log.map((l, i) => <div key={i}>{l}</div>)}
          </div>
        </section>
      </div>

      <p className="op-foot">
        Display: <a href="/">/</a> · Language lock &amp; fallback need a bot-side
        <code> on_client_message </code> handler (Phase 3).
      </p>
    </div>
  );
}
