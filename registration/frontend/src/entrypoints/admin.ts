import { connectToMqtt } from "../admin/mqtt";
import "../admin/scan-actions";
import renderCart from "../admin/cart";

export interface ApisConfig {
  debug: boolean;
  printer_uri: string;
  mqtt: ApisMqttConfig;
  urls: ApisUrls;
}

export interface ApisMqttConfig {
  broker: string;
  auth: ApisMqttAuth;
}

export interface ApisMqttAuth {
  user: string;
  token: string;
  base_topic: string;
}

export interface ApisUrls {
  onsite_add_to_cart: string;
  onsite_admin_cart: string;
  onsite_admin_clear_cart: string;
  onsite_remove_from_cart: string;
  registration_badge_change: string;
}

declare global {
  const APIS_CONFIG: ApisConfig;
}

if (APIS_CONFIG.mqtt) {
  connectToMqtt(APIS_CONFIG.mqtt)
}

renderCart(APIS_CONFIG);
