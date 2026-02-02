import { Toast } from "@kobalte/core/toast";
import * as Sentry from "@sentry/solid";
import { createSignal } from "solid-js";
import { For, render } from "solid-js/web";
import "vite/modulepreload-polyfill";

import type { ApisConfig } from "../admin";
import { Navbar } from "../admin/Navbar";
import { Onsite } from "../admin/Onsite";
import { CartManager } from "../admin/cart";
import "../admin/index.scss";
import MqttClient from "../admin/mqtt";
import { ConfigContext } from "../admin/providers/config-provider";
import {
  UserSettingsContext,
  UserSettingsManager,
} from "../admin/providers/user-settings-provider";

declare global {
  const APIS_CONFIG: ApisConfig;
}

if (APIS_CONFIG.sentry.enabled) {
  Sentry.init({
    dsn: APIS_CONFIG.sentry.frontend_dsn,
    environment: APIS_CONFIG.sentry.environment,
    release: APIS_CONFIG.sentry.release,
    beforeSend(event) {
      if (APIS_CONFIG.sentry.user_reports && event.exception) {
        Sentry.showReportDialog({ eventId: event.event_id });
      }

      return event;
    },
  });

  Sentry.setUser({
    id: APIS_CONFIG.user.id,
    email: APIS_CONFIG.user.email,
  });

  if (APIS_CONFIG.user.station) {
    Sentry.setTag("onsite_station", APIS_CONFIG.user.station);
  }
}

function start() {
  const elem = document.getElementById("onsite");
  if (!elem) {
    return alert("Missing core page component");
  }

  let mqtt: MqttClient;
  let cartManager: CartManager;
  let userSettings: UserSettingsManager;

  try {
    mqtt = new MqttClient(APIS_CONFIG.mqtt);
    cartManager = new CartManager(APIS_CONFIG.urls, mqtt);
    userSettings = new UserSettingsManager();
  } catch (err: any) {
    render(() => {
      return (
        <div>
          <h1>Error</h1>
          <p>Something went wrong during page initialization.</p>
          <pre>{err.toString()}</pre>
        </div>
      );
    }, elem);
    return;
  }

  const [readyForNext, setReadyForNext] = createSignal(false);

  render(() => {
    return (
      <ConfigContext.Provider value={APIS_CONFIG}>
        <UserSettingsContext.Provider value={userSettings}>
          <Navbar setReadyForNext={setReadyForNext} cartManager={cartManager} />

          <For each={APIS_CONFIG.errors}>
            {(error) => (
              <div class={`notification m-3 is-${error.type}`} role="alert">
                {error.text}
              </div>
            )}
          </For>

          <div
            classList={{
              "container py-3": !userSettings.userSettings().container_fluid,
              "container-fluid p-3":
                userSettings.userSettings().container_fluid,
            }}
          >
            <Onsite
              mqtt={mqtt}
              cartManager={cartManager}
              readyForNext={readyForNext}
              setReadyForNext={setReadyForNext}
            />
          </div>

          <Toast.Region>
            <Toast.List as="div" class="toast-container" />
          </Toast.Region>
        </UserSettingsContext.Provider>
      </ConfigContext.Provider>
    );
  }, elem);
}

start();
