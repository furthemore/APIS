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

  const [clearing, setClearing] = createSignal<boolean>(false);
  const clear = async () => {
    setClearing(true);
    await props.cartManager.clearCart();
    setClearing(false);
  };

  const [removeBadgeId, setRemoveBadgeId] = createSignal<number>();
  const [remove] = createResource(removeBadgeId, async (id) => {
    await props.cartManager.removeBadge(id);
  });

  const anythingLoading = () =>
    refresh.loading || clearing() || remove.loading;

  createShortcut(["Alt", "R"], () => {
    if (anythingLoading()) return;
    refetchCart();
  });

  createShortcut(["Alt", "A"], () => {
    if (anythingLoading()) return;
    clear();
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
                classList={{ "is-loading": clearing() }}
                disabled={anythingLoading()}
                title="Alt+A"
                onClick={clear}
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
