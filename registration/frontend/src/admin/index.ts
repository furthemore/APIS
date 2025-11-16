import * as Sentry from "@sentry/solid";
import { ErrorBoundary } from "solid-js";

export interface ApisConfig {
  user: ApisUser;
  sentry: ApisSentry;
  errors: ApisError[];
  mqtt: ApisMqttConfig;
  shirt_sizes: ApisShirtSize[];
  urls: ApisUrls;
  permissions: ApisPermissions;
  terminals: ApisTerminalSettings;
}

export interface ApisUser {
  id: number;
  email: string;
  station?: string;
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
}

export interface ApisMqttAuth {
  user: string;
  token: string;
  base_topic: string;
  print_topic?: string;
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
  onsite_admin_transfer_cart: string;
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
  selected?: ApisSelectedTerminal;
  available: ApisTerminal[];
}

export interface ApisSelectedTerminal {
  id: number;
  features: ApisTerminalFeatures;
}

export interface ApisTerminalFeatures {
  print_via_mqtt: boolean;
  square_terminal: boolean;
  payment_type?: "mqtt-app" | "square-terminal";
  cashdrawer: boolean;
}

export interface ApisTerminal {
  id: number;
  name: string;
}

export const CSRF_TOKEN = document.querySelector<HTMLMetaElement>(
  "meta[name='csrf_token']",
)!.content;

export const SentryErrorBoundary =
  Sentry.withSentryErrorBoundary(ErrorBoundary);
