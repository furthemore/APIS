import { connectToMqtt } from "../admin/mqtt";
import "../admin/scan-actions";
import createCart from "../admin/cart";

export interface ApisConfig {
  debug: boolean;
  printer_uri: string;
  mqtt: ApisMqttConfig;
  urls: ApisUrls;
  permissions: ApisPermissions;
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
  complete_cash_transaction: string;
  enable_payment: string;
  onsite_add_to_cart: string;
  onsite_admin_cart: string;
  onsite_admin_clear_cart: string;
  onsite_print_badges: string;
  onsite_remove_from_cart: string;
  registration_badge_change: string;
  pdf: string;
}

export interface ApisPermissions {
  cash: boolean;
  discount: boolean;
}

declare global {
  const APIS_CONFIG: ApisConfig;
}

if (APIS_CONFIG.mqtt) {
  connectToMqtt(APIS_CONFIG.mqtt)
}

createCart(APIS_CONFIG);
