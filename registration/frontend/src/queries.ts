import { QueryClient } from "@tanstack/solid-query";
import ky from "ky";

import { CSRF_TOKEN } from "./common";

export const api = ky.extend({
  redirect: "error",
  prefixUrl: window.location.origin,
  hooks: {
    beforeRequest: [
      (request) => {
        request.headers.set("x-csrftoken", CSRF_TOKEN);
      },
    ],
  },
});

export const queryClient = new QueryClient();
