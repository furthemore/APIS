import { Component, createResource, createSignal } from "solid-js";
import { createShortcut } from "@solid-primitives/keyboard";
import { Show } from "solid-js/web";

import { CartActions } from "./CartActions";
import { CartEntries } from "./CartEntries";
import { CartManager } from "../cart-manager";

export const Cart: Component<{
  cartManager: CartManager;
}> = (props) => {
  const [refresh, { refetch: refetchCart }] = createResource(
    async () => await props.cartManager.refreshCart()
  );

  // Clearing the cart gets some weird handling because we don't want the
  // request to immediately be made. Instead, create a signal for the initial
  // request and hold onto the refetch function. When the initial request has
  // been made, use refetch instead of setting the signal.

  const [clearCart, setClearCart] = createSignal<boolean>(false);
  const [clear, { refetch: refetchClear }] = createResource(
    clearCart,
    async () => await props.cartManager.clearCart()
  );

  const doClearCart = () => {
    if (clearCart()) {
      refetchClear();
    } else {
      setClearCart(true);
    }
  };

  const [removeBadgeId, setRemoveBadgeId] = createSignal<number>();
  const [remove] = createResource(removeBadgeId, async (id) => {
    await props.cartManager.removeBadge(id);
  });

  const anythingLoading = () =>
    refresh.loading || clear.loading || remove.loading;

  createShortcut(["Alt", "R"], () => {
    if (anythingLoading()) return;
    refetchCart();
  });

  createShortcut(["Alt", "A"], () => {
    if (anythingLoading()) return;
    doClearCart();
  });

  createShortcut(["Alt", "\\"], () => {
    if (anythingLoading()) return;

    const lastBadge = props.cartManager.cartEntries()?.result?.at(-1);
    if (!lastBadge) return;

    setRemoveBadgeId(lastBadge.id);
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
                onClick={refetchCart}
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
                onClick={doClearCart}
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
          entries={props.cartManager.cartEntries()}
        />
      </div>

      <Show when={props.cartManager.cartEntries()}>
        <CartEntries
          manager={props.cartManager}
          entries={props.cartManager.cartEntries()}
        />
      </Show>
    </div>
  );
};
