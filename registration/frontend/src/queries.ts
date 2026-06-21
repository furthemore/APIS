import { QueryClient } from "@tanstack/solid-query";
import ky from "ky";

import { CSRF_TOKEN } from "./common";

const MUTATING_METHODS = new Set(["put", "delete", "post", "patch", "connect"]);

export const api = ky.extend({
  prefix: import.meta.env.VITE_API_PREFIX_URL || globalThis.location.origin,
  hooks: {
    beforeRequest: [
      ({ request }: { request: Request }) => {
        if (MUTATING_METHODS.has(request.method.toLowerCase())) {
          if (!request.headers.has("idempotency-key")) {
            request.headers.set(
              "idempotency-key",
              globalThis.crypto.randomUUID(),
            );
          }

          if (CSRF_TOKEN) {
            request.headers.set("x-csrftoken", CSRF_TOKEN);
          }
        }
      },
    ],
  },
});

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
    },
  },
});
