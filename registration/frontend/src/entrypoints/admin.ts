import createActions from "../admin/Navbar";
import createOnsiteExperience from "../admin/Onsite";

import "../admin/index.scss";

export const CSRF_TOKEN = document.querySelector<HTMLMetaElement>(
  "meta[name='csrf_token']"
).content;

export interface ApisConfig {
  debug: boolean;
  printer_uri: string;
  mqtt: ApisMqttConfig;
  urls: ApisUrls;
  permissions: ApisPermissions;
  terminals: ApisTerminalSettings;
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

createActions(APIS_CONFIG);
createOnsiteExperience(APIS_CONFIG);
