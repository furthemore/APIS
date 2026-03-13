import { QueryClientProvider } from "@tanstack/solid-query";
import { RouterProvider, createRouter } from "@tanstack/solid-router";
import "solid-devtools";
import { render } from "solid-js/web";
import "vite/modulepreload-polyfill";

import "./index.scss";
import { queryClient } from "./queries";
import { routeTree } from "./routeTree.gen";
import { initSentry } from "./sentry";

const router = createRouter({
  routeTree,
  context: { queryClient },
  scrollRestoration: true,
  defaultPreload: "intent",
  defaultPreloadStaleTime: 0,
});

declare module "@tanstack/solid-router" {
  interface Register {
    router: typeof router;
  }
}

initSentry();

const rootElement = document.getElementById("root")!;
render(
  () => (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  ),
  rootElement,
);
