"use client";

import { useEffect, useState } from "react";
import { PipecatClientProvider } from "@pipecat-ai/client-react";
import { createClient } from "@/lib/pipecatClient";

// client-react bundles its own (nominal) copy of client-js's PipecatClient type, so we
// derive the exact type the provider expects rather than importing it from client-js.
type ProviderClient = React.ComponentProps<typeof PipecatClientProvider>["client"];

export function Providers({ children }: { children: React.ReactNode }) {
  // The WebRTC client touches browser-only APIs in its constructor, so it must be created
  // in the browser — never during static prerender. Until it exists we render a light
  // shell, which keeps the children (and their WebRTC hooks) out of the server render.
  const [client, setClient] = useState<ProviderClient | null>(null);

  useEffect(() => {
    setClient(createClient() as unknown as ProviderClient);
  }, []);

  if (!client) {
    return (
      <main className="stage">
        <div className="attract">
          <div className="brand">{"LYNK & CO"}</div>
          <p>Loading…</p>
        </div>
      </main>
    );
  }

  return <PipecatClientProvider client={client}>{children}</PipecatClientProvider>;
}
