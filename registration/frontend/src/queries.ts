import { QueryClient } from "@tanstack/solid-query";
import ky from "ky";

import { CSRF_TOKEN } from "./common";

export const api = ky.extend({
  prefixUrl: import.meta.env.VITE_API_PREFIX_URL || window.location.origin,
  hooks: {
    beforeRequest: [
      (request) => {
        if (request.method.toLowerCase() === "post" && CSRF_TOKEN) {
          request.headers.set("x-csrftoken", CSRF_TOKEN);
        }
      },
    ],
  },
});

export const queryClient = new QueryClient();
