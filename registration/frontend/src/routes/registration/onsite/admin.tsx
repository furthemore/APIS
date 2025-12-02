import { Toast } from "@kobalte/core/toast";
import { useQuery } from "@tanstack/solid-query";
import { createFileRoute, getRouteApi } from "@tanstack/solid-router";
import {
  type Component,
  Show,
  createMemo,
  createSignal,
  onCleanup,
} from "solid-js";
import { Portal } from "solid-js/web";

import {
  type OnsiteAdminSearch,
  contextQueryOptions,
} from "../../../admin/api";
import { Navbar } from "../../../admin/components/navbar";
import { Onsite } from "../../../admin/components/onsite";
import MqttClient from "../../../admin/mqtt";
import { ConfigContext } from "../../../admin/providers/config-provider";
import { MqttContext } from "../../../admin/providers/mqtt-provider";
import {
  UserSettingsContext,
  UserSettingsManager,
} from "../../../admin/providers/user-settings-provider";
import { Container } from "../../../components/container";
import { queryClient } from "../../../queries";

const OnsiteAdmin: Component = () => {
  const route = getRouteApi("/registration/onsite/admin");
  const search = route.useSearch();

  const [readyForNext, setReadyForNext] = createSignal(false);

  const query = useQuery(() => contextQueryOptions(search().terminal));

  const userSettings = createMemo(() => new UserSettingsManager());

  const mqtt = createMemo(() => {
    const config = query.data?.mqtt;
    if (!config) return;

    const m = new MqttClient();
    m.connect(config);

    onCleanup(() => {
      m.disconnect();
    });

    return m;
  });

  return (
    <ConfigContext.Provider value={query.data}>
      <UserSettingsContext.Provider value={userSettings}>
        <Navbar setReadyForNext={setReadyForNext} />

        <Container>
          <Show when={query.status === "success"} fallback={<ContextLoading />}>
            <MqttConnecting mqtt={mqtt()} />

            <MqttContext.Provider value={mqtt}>
              <Onsite
                readyForNext={readyForNext()}
                setReadyForNext={setReadyForNext}
              />
            </MqttContext.Provider>
          </Show>
        </Container>

        <Portal>
          <Toast.Region>
            <Toast.List as="div" class="toast-container end-0 bottom-0 p-3" />
          </Toast.Region>
        </Portal>
      </UserSettingsContext.Provider>
    </ConfigContext.Provider>
  );
};

const ContextLoading: Component = () => {
  return (
    <div class="alert alert-warning">
      <span>Loading</span>{" "}
      <div class="spinner-border spinner-border-sm" role="status" />
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
          <span>Connecting to MQTT</span>{" "}
          <div class="spinner-border" role="status" />
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
      terminal: search?.terminal ? Number(search.terminal) : undefined,
    };
  },
  loaderDeps: ({ search: { terminal } }) => ({ terminal }),
  loader: ({ deps: { terminal } }) =>
    queryClient.ensureQueryData(contextQueryOptions(terminal)),
  component: OnsiteAdmin,
});
