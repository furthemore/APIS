import { createSignal } from "solid-js";
import { render } from "solid-js/web";

import { CartManager, CartResponse } from "./cart-manager";
import { ApisConfig } from "../../entrypoints/admin";
import { Cart } from "./components/Cart";
import { ConfigContext } from "../providers/config-provider";

const [cartEntries, setCartEntries] = createSignal<CartResponse | null>(null);

export let cartManager: CartManager | null = null;

export default function createCart(config: ApisConfig) {
  cartManager = new CartManager(config.urls, setCartEntries);
  window["cartManager"] = cartManager;

  render(() => {
    return (
      <ConfigContext.Provider value={config}>
        <Cart cartManager={cartManager} cartEntries={cartEntries()} />
      </ConfigContext.Provider>
    );
  }, document.getElementById("cart"));
}
