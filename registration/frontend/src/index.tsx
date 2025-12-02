import { RouterProvider, createRouter } from "@tanstack/solid-router";
import "solid-devtools";
import { render } from "solid-js/web";
import "vite/modulepreload-polyfill";

import "./index.scss";
import { routeTree } from "./routeTree.gen";

const router = createRouter({ routeTree });

declare module "@tanstack/solid-router" {
  interface Register {
    router: typeof router;
  }
}

const rootElement = document.getElementById("root")!;
render(() => <RouterProvider router={router} />, rootElement);
