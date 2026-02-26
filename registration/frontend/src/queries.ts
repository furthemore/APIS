import { QueryClient } from "@tanstack/solid-query";
import ky from "ky";

import { CSRF_TOKEN } from "./common";

const MUTATING_METHODS = new Set(["put", "delete", "post", "patch", "connect"]);

export const api = ky.extend({
  prefixUrl: import.meta.env.VITE_API_PREFIX_URL || window.location.origin,
  hooks: {
    beforeRequest: [
      (request) => {
        if (MUTATING_METHODS.has(request.method.toLowerCase())) {
          if (!request.headers.has("idempotency-key")) {
            request.headers.set("idempotency-key", window.crypto.randomUUID());
          }

          if (CSRF_TOKEN) {
            request.headers.set("x-csrftoken", CSRF_TOKEN);
          }
        }
      },
    ],
  },
});

export const queryClient = new QueryClient();
