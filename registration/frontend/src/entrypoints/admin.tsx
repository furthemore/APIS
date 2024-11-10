import { For, render } from "solid-js/web";

import { ConfigContext } from "../admin/providers/config-provider";
import { Navbar } from "../admin/Navbar";
import { Onsite } from "../admin/Onsite";

import "../admin/index.scss";
import MqttClient from "../admin/mqtt";
import { CartManager } from "../admin/cart";
import {
  UserSettingsContext,
  UserSettingsManager,
} from "../admin/providers/user-settings-provider";

export const CSRF_TOKEN = document.querySelector<HTMLMetaElement>(
  "meta[name='csrf_token']"
)!.content;

export interface ApisConfig {
  debug: boolean;
  errors: ApisError[];
  printer_uri: string;
  mqtt: ApisMqttConfig;
  urls: ApisUrls;
  permissions: ApisPermissions;
  terminals: ApisTerminalSettings;
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

export interface ApisUrls {
  assign_badge_number: string;
  cash_deposit: string;
  cash_pickup: string;
  close_drawer: string;
  close_terminal: string;
  complete_cash_transaction: string;
  enable_payment: string;
  logout: string;
  no_sale: string;
  onsite_add_to_cart: string;
  onsite_admin_cart: string;
  onsite_admin_clear_cart: string;
  onsite_admin_search: string;
  onsite_admin: string;
  onsite_print_badges: string;
  onsite_print_clear: string;
  onsite_remove_from_cart: string;
  onsite: string;
  open_drawer: string;
  open_terminal: string;
  pdf: string;
  ready_terminal: string;
  registration_badge_change: string;
  safe_drop: string;
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

declare global {
  const APIS_CONFIG: ApisConfig;
}

function start() {
  const mqtt = new MqttClient(APIS_CONFIG.mqtt);
  const cartManager = new CartManager(APIS_CONFIG.urls, mqtt);

  const userSettings = new UserSettingsManager();

  render(() => {
    return (
      <ConfigContext.Provider value={APIS_CONFIG}>
        <UserSettingsContext.Provider value={userSettings}>
          <Navbar />

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
            <Onsite mqtt={mqtt} cartManager={cartManager} />
          </div>
        </UserSettingsContext.Provider>
      </ConfigContext.Provider>
    );
  }, document.getElementById("onsite")!);
}

start();
