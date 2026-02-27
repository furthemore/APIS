import { TanStackDevtools } from "@tanstack/solid-devtools";
import { hotkeysDevtoolsPlugin } from "@tanstack/solid-hotkeys-devtools";
import type { QueryClient } from "@tanstack/solid-query";
import { SolidQueryDevtoolsPanel } from "@tanstack/solid-query-devtools";
import {
  HeadContent,
  Outlet,
  createRootRouteWithContext,
} from "@tanstack/solid-router";
import { TanStackRouterDevtoolsPanel } from "@tanstack/solid-router-devtools";
import { type Component } from "solid-js";

const RootLayout: Component = () => {
  return (
    <>
      <HeadContent />
      <Outlet />
      <TanStackDevtools
        plugins={[
          {
            name: "TanStack Query",
            render: <SolidQueryDevtoolsPanel />,
          },
          {
            name: "TanStack Router",
            render: <TanStackRouterDevtoolsPanel />,
          },
          hotkeysDevtoolsPlugin(),
        ]}
        config={{ position: "bottom-left" }}
      />
    </>
  );
};

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()(
  {
    component: RootLayout,
  },
);
