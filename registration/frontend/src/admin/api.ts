import ky from "ky";

import { CSRF_TOKEN } from "../entrypoints/admin";

const MUTATING_METHODS = new Set(["put", "delete", "post", "patch", "connect"]);

export type FallibleRequest<T> =
  | {
      success: false;
      reason?: string;
    }
  | ({ success: true } & T);

export const api = ky.extend({
  hooks: {
    beforeRequest: [
      (request) => {
        console.debug(`Making ${request.method} request to ${request.url}`);

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
    afterResponse: [
      (request, _options, response) => {
        console.debug(`Got ${response.status} response from ${request.url}`);

        if (response.redirected && response.url.includes("/accounts/login")) {
          const url = new URL(response.url);
          url.searchParams.set(
            "next",
            window.location.pathname + window.location.search,
          );
          window.location.href = url.toString();
        }
      },
    ],
  },
});
