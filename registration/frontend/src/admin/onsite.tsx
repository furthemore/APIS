import { Component, createSignal, onCleanup, useContext } from "solid-js";
import { render } from "solid-js/web";

import { ApisConfig } from "../entrypoints/admin";
import { ConfigContext } from "./providers/config-provider";
import { AttendeeSearch } from "./attendee-search";
import { CartManager, CartResponse } from "./cart/cart-manager";
import { Cart } from "./cart/components/Cart";
import { ScanPanel } from "./scan-actions";

const Onsite: Component = () => {
  const config = useContext(ConfigContext);

  const [cartEntries, setCartEntries] = createSignal<CartResponse | null>();
  const cartManager = new CartManager(config.urls, setCartEntries);

  onCleanup(() => {
    cartManager.close();
  });

  const [searchQuery, setSearchQuery] = createSignal<string>();

  return (
    <div class="columns">
      <div class="column is-half is-narrow-tablet">
        <AttendeeSearch
          cartManager={cartManager}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />

        <ScanPanel gotScannedName={(name) => setSearchQuery(name)} />
      </div>

      <div class="column is-half is-narrow-tablet">
        <Cart cartManager={cartManager} cartEntries={cartEntries()} />
      </div>
    </div>
  );
};

export default function createOnsiteExperience(config: ApisConfig) {
  render(
    () => (
      <ConfigContext.Provider value={config}>
        <Onsite />
      </ConfigContext.Provider>
    ),
    document.getElementById("onsite")
  );
}
