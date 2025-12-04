import type { QueryClient } from "@tanstack/solid-query";
import { SolidQueryDevtools } from "@tanstack/solid-query-devtools";
import { Outlet, createRootRouteWithContext } from "@tanstack/solid-router";
import { TanStackRouterDevtools } from "@tanstack/solid-router-devtools";
import { type Component } from "solid-js";

const RootLayout: Component = () => {
  return (
    <>
      <Outlet />
      <SolidQueryDevtools />
      <TanStackRouterDevtools />
    </>
  );
};

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()(
  {
    component: RootLayout,
  },
);
