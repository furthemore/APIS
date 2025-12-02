import { QueryClientProvider } from "@tanstack/solid-query";
import { SolidQueryDevtools } from "@tanstack/solid-query-devtools";
import { Outlet, createRootRoute } from "@tanstack/solid-router";
import { TanStackRouterDevtools } from "@tanstack/solid-router-devtools";
import type { Component } from "solid-js";

import { queryClient } from "../queries";

const RootLayout: Component = () => {
  return (
    <>
      <QueryClientProvider client={queryClient}>
        <Outlet />
        <TanStackRouterDevtools />
        <SolidQueryDevtools />
      </QueryClientProvider>
    </>
  );
};

export const Route = createRootRoute({ component: RootLayout });
