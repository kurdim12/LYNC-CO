import { useRTVIClientEvent } from "@pipecat-ai/client-react";
import type { RTVIEvent } from "@pipecat-ai/client-js";

// client-react bundles its OWN nominal copy of client-js's `RTVIEvent` enum (its rolled-up
// .d.ts), which TypeScript treats as incompatible with the one we import from client-js —
// even though the runtime string values are identical. This thin re-type lets us call the
// hook with client-js's RTVIEvent and an explicitly-typed handler. Runtime behaviour is
// unchanged; we only relax the (spurious, dual-package) type error.
export const useLivEvent = useRTVIClientEvent as unknown as <H extends (...args: never[]) => void>(
  event: RTVIEvent,
  handler: H,
) => void;
