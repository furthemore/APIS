import { Toast } from "@kobalte/core/toast";
import * as Sentry from "@sentry/solid";
import { MultiProvider } from "@solid-primitives/context";
import { HotkeysProvider } from "@tanstack/solid-hotkeys";
import { useQuery } from "@tanstack/solid-query";
import { createFileRoute, getRouteApi } from "@tanstack/solid-router";
import {
  type Component,
  Match,
  Show,
  Switch,
  createEffect,
  createMemo,
  createSignal,
  onCleanup,
} from "solid-js";
import { Portal } from "solid-js/web";

import {
  type OnsiteAdminSearch,
  contextQueryOptions,
  terminalQueryOptions,
} from "@admin/api";
import { Navbar } from "@admin/features/navbar";
import { Onsite } from "@admin/features/onsite";
import { TerminalSelection } from "@admin/features/terminal-selection";
import MqttClient from "@admin/mqtt";
import { ConfigContext } from "@admin/providers/config-provider";
import { MqttContext } from "@admin/providers/mqtt-provider";
import {
  UserSettingsContext,
  UserSettingsManager,
} from "@admin/providers/user-settings-provider";
import { Container } from "@components/container";

import { setCurrentUser } from "../../../sentry";

const OnsiteAdmin: Component = () => {
  const route = getRouteApi("/registration/onsite/admin");
  const search = route.useSearch();

  const [readyForNext, setReadyForNext] = createSignal(false);

  const context = useQuery(() => contextQueryOptions(search().terminal));

  const userSettings = createMemo(() => new UserSettingsManager());

  const mqtt = createMemo(() => {
    const config = context.data?.mqtt;
    if (!config) return;

    const m = new MqttClient();
    m.connect(config);

    onCleanup(() => {
      m.disconnect();
    });

    return m;
  });

  createEffect(() => {
    const config = context.data;
    if (!config) return;

    const terminalName = config.terminals.available.find(
      (terminal) => terminal.id === config.terminals.selected?.id,
    )?.name;

    Sentry.setTag("terminal", terminalName);
    Sentry.setUser({
      id: config.user.id,
      email: config.user.email,
    });
    setCurrentUser({
      email: config.user.email,
      name: terminalName,
    });

    onCleanup(() => {
      Sentry.setTag("terminal", undefined);
      Sentry.setUser(null);
      setCurrentUser(undefined);
    });
  });

  return (
    <HotkeysProvider
      defaultOptions={{ hotkey: { preventDefault: true, ignoreInputs: false } }}
    >
      <MultiProvider
        values={[
          [ConfigContext, () => context.data],
          [UserSettingsContext, userSettings],
          [MqttContext, mqtt],
        ]}
      >
        <Navbar setReadyForNext={setReadyForNext} />

        <Container>
          <Switch fallback={<ContextLoading />}>
            <Match when={search().terminal === undefined}>
              <TerminalSelection />
            </Match>
            <Match when={context.isEnabled && context.isFetched}>
              <MqttConnecting mqtt={mqtt()} />

              <Onsite
                readyForNext={readyForNext()}
                setReadyForNext={setReadyForNext}
              />
            </Match>
          </Switch>
        </Container>

        <Portal>
          <Toast.Region>
            <Toast.List as="div" class="toast-container end-0 bottom-0 p-3" />
          </Toast.Region>
        </Portal>
      </MultiProvider>
    </HotkeysProvider>
  );
};

const ContextLoading: Component = () => {
  return (
    <div class="alert alert-warning my-3">
      <span>Loading</span> <div class="spinner-border spinner-border-sm" />
    </div>
  );
};

const MqttConnecting: Component<{ mqtt?: MqttClient }> = (props) => {
  const errorMessage = () => props.mqtt?.errorMessage();
  const errorClasses = () =>
    errorMessage() ? "alert-danger" : "alert-warning";

  return (
    <Show when={!props.mqtt?.isConnected()}>
      <div class={`alert my-3 ${errorClasses()}`}>
        <h4 class="alert-heading d-flex align-items-center column-gap-2">
          <span>Connecting to MQTT</span> <div class="spinner-border" />
        </h4>

        <p>
          Please wait, scans and cart actions will not work until connected.
        </p>

        <Show when={errorMessage()}>
          <p>
            <code>{errorMessage()}</code>
          </p>
        </Show>
      </div>
    </Show>
  );
};

export const Route = createFileRoute("/registration/onsite/admin")({
  validateSearch: (search): OnsiteAdminSearch => {
    return {
      terminal: search.terminal ? Number(search.terminal) : undefined,
    };
  },
  loaderDeps: ({ search: { terminal } }) => ({ terminal }),
  loader: ({ deps: { terminal }, context: { queryClient } }) => {
    if (terminal) {
      return queryClient.ensureQueryData(contextQueryOptions(terminal));
    } else {
      return queryClient.ensureQueryData(terminalQueryOptions());
    }
  },
  head: ({ loaderData }) => {
    const meta = [];

    if (
      loaderData &&
      "selected" in loaderData.terminals &&
      loaderData.terminals.selected
    ) {
      const selectedId = loaderData.terminals.selected.id;
      const terminalName =
        loaderData.terminals.available.find(
          (terminal) => terminal.id == selectedId,
        )?.name || "Unknown";

      meta.push({ title: `${terminalName} · Onsite Registration Admin` });
    } else {
      meta.push({ title: "Onsite Registration Admin" });
    }

    return { meta };
  },
  component: OnsiteAdmin,
});
