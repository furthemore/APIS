import { Component, createEffect, createResource } from "solid-js";
import { createShortcut } from "@solid-primitives/keyboard";
import { Show } from "solid-js/web";

import { CartActions } from "./CartActions";
import { CartEntries } from "./CartEntries";
import { CartManager } from "../cart-manager";

export const Cart: Component<{
  cartManager: CartManager;
}> = (props) => {
  const [refresh, { refetch: refreshCart }] = createResource(async () => {
    await props.cartManager.refreshCart();
  });

  const [clear, { refetch: clearCart }] = createResource(async () => {
    await props.cartManager.clearCart();
  });

  const anythingLoading = () => refresh.loading || clear.loading;

  createEffect(() => {
    refreshCart();
  });

  createShortcut(["Alt", "A"], () => {
    if (anythingLoading()) return;
    clearCart();
  });

  createShortcut(["Alt", "R"], () => {
    if (anythingLoading()) return;
    refreshCart();
  });

  return (
    <div class="panel is-dark">
      <div class="panel-heading">
        <div class="columns is-mobile">
          <div class="column is-align-self-center">Cart</div>

          <div class="column is-narrow">
            <div class="buttons">
              <button
                class="button is-primary is-small"
                classList={{ "is-loading": refresh.loading }}
                disabled={anythingLoading()}
                title="Alt+R"
                onClick={(ev) => {
                  ev.preventDefault();
                  refreshCart();
                }}
              >
                <span class="icon">
                  <i class="fas fa-sync"></i>
                </span>
              </button>

              <button
                class="button is-warning is-small"
                classList={{ "is-loading": clear.loading }}
                disabled={anythingLoading()}
                title="Alt+A"
                onClick={() => clearCart()}
              >
                <span class="icon">
                  <i class="fas fa-xmark"></i>
                </span>
                <span>Clear</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="panel-block">
        <CartActions
          manager={props.cartManager}
          cartEntries={props.cartManager.cartEntries()}
        />
      </div>

      <Show when={props.cartManager.cartEntries()}>
        <CartEntries
          manager={props.cartManager}
          cart={props.cartManager.cartEntries()}
        />
      </Show>
    </div>
  );
};
