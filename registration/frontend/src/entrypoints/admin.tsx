import * as Sentry from "@sentry/solid";
import { createSignal } from "solid-js";
import { ErrorBoundary, For, render } from "solid-js/web";

import { Navbar } from "../admin/Navbar";
import { Onsite } from "../admin/Onsite";
import { ConfigContext } from "../admin/providers/config-provider";

import { CartManager } from "../admin/cart";
import "../admin/index.scss";
import MqttClient from "../admin/mqtt";
import {
  UserSettingsContext,
  UserSettingsManager,
} from "../admin/providers/user-settings-provider";

declare global {
  const APIS_CONFIG: ApisConfig;
}

export interface ApisConfig {
  debug: boolean;
  sentry: ApisSentry;
  errors: ApisError[];
  mqtt: ApisMqttConfig;
  shirt_sizes: ApisShirtSize[];
  urls: ApisUrls;
  permissions: ApisPermissions;
  terminals: ApisTerminalSettings;
}

export interface ApisSentry {
  enabled: boolean;
  user_reports: boolean;
  frontend_dsn?: string;
  environment?: string;
  release?: string;
}

export interface ApisError {
  type: string;
  text: string;
}

export interface ApisMqttConfig {
  broker: string;
  auth: ApisMqttAuth;
  supports_printing: boolean;
}

export interface ApisMqttAuth {
  user: string;
  token: string;
  base_topic: string;
}

export interface ApisShirtSize {
  id: number;
  name: string;
}

export interface ApisUrls {
  assign_badge_number: string;
  cash_deposit: string;
  cash_pickup: string;
  close_drawer: string;
  complete_cash_transaction: string;
  enable_payment: string;
  logout: string;
  no_sale: string;
  onsite_add_to_cart: string;
  onsite_admin_cart: string;
  onsite_admin_clear_cart: string;
  onsite_admin_search: string;
  onsite_admin: string;
  onsite_create_discount: string;
  onsite_print_badges: string;
  onsite_print_clear: string;
  onsite_print_receipts: string;
  onsite_remove_from_cart: string;
  onsite: string;
  open_drawer: string;
  pdf: string;
  registration_badge_change: string;
  safe_drop: string;
  set_terminal_status: string;
}

export interface ApisPermissions {
  cash: boolean;
  cash_admin: boolean;
  discount: boolean;
}

export interface ApisTerminalSettings {
  selected?: number;
  available: ApisTerminal[];
}

export interface ApisTerminal {
  id: number;
  name: string;
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
}

export const SentryErrorBoundary =
  Sentry.withSentryErrorBoundary(ErrorBoundary);

export const CSRF_TOKEN = document.querySelector<HTMLMetaElement>(
  "meta[name='csrf_token']"
)!.content;

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
          <Navbar setReadyForNext={setReadyForNext} />

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
        </UserSettingsContext.Provider>
      </ConfigContext.Provider>
    );
  }, elem);
}

start();
