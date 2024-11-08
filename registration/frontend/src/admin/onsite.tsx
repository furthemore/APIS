import { Component, createSignal } from "solid-js";
import { render } from "solid-js/web";

import { ApisConfig } from "../entrypoints/admin";
import { AttendeeSearch } from "./attendee-search";
import { Cart, CartManager } from "./cart";
import { ConfigContext } from "./providers/config-provider";
import { ScanPanel } from "./scan";
import MqttClient from "./mqtt";

const Onsite: Component<{ mqtt: MqttClient; cartManager: CartManager }> = (
  props
) => {
  const [searchQuery, setSearchQuery] = createSignal<string>();

  return (
    <div class="columns">
      <div class="column is-half is-narrow-tablet">
        <AttendeeSearch
          cartManager={props.cartManager}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />

        <ScanPanel
          gotScannedName={(name) => setSearchQuery(name)}
          emitter={props.mqtt.emitter}
        />
      </div>

      <div class="column is-half is-narrow-tablet">
        <Cart cartManager={props.cartManager} />
      </div>
    </div>
  );
};

export default function createOnsiteExperience(config: ApisConfig) {
  const mqtt = new MqttClient(config.mqtt);
  const cartManager = new CartManager(config.urls, mqtt);

  render(
    () => (
      <ConfigContext.Provider value={config}>
        <Onsite mqtt={mqtt} cartManager={cartManager} />
      </ConfigContext.Provider>
    ),
    document.getElementById("onsite")
  );
}
