import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { OFFER_ENDPOINT } from "./config";

// One factory so the display and the operator dashboard build the client identically.
//
// Transport note: we use SmallWebRTC (the bot's built-in transport — zero extra
// accounts, works against `python bot.py` immediately). For a robust *public* hosted
// setup you may switch to the Daily transport (@pipecat-ai/daily-transport) to get
// managed TURN/SFU — see DEPLOY.md. The PipecatClient API is identical; only the
// transport instance and connect params change.
export function createClient(): PipecatClient {
  return new PipecatClient({
    transport: new SmallWebRTCTransport(),
    enableMic: true,
    enableCam: false,
  });
}

// SmallWebRTC connect params: POST the SDP offer to the bot's /api/offer endpoint.
export const connectParams = { webrtcRequestParams: { endpoint: OFFER_ENDPOINT } };
