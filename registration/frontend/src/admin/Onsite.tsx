import { Component, createSignal } from "solid-js";
import { render } from "solid-js/web";

import { ApisConfig } from "../entrypoints/admin";
import { AttendeeSearch } from "./attendee-search";
import { Cart, CartManager } from "./cart";
import { ConfigContext } from "./providers/config-provider";
import { ScanPanel } from "./scan";
import MqttClient from "./mqtt";

export const Onsite: Component<{
  mqtt: MqttClient;
  cartManager: CartManager;
}> = (props) => {
  const [searchQuery, setSearchQuery] = createSignal<string>();

  return (
    <div class="columns">
      <div class="column is-three-fifths is-narrow-tablet">
        <AttendeeSearch
          cartManager={props.cartManager}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />

        <ScanPanel
          gotScannedName={(name, birthday) => {
            const query = birthday ? `${name} birthday:${birthday}` : name;
            setSearchQuery(query);
          }}
          emitter={props.mqtt.emitter}
        />
      </div>

      <div class="column is-two-fifths is-narrow-tablet">
        <Cart
          cartManager={props.cartManager}
          clearSearch={() => setSearchQuery("")}
        />
      </div>
    </div>
  );
};
