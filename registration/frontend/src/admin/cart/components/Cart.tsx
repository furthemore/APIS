import { createShortcut } from "@solid-primitives/keyboard";
import { Component, createResource, createSignal } from "solid-js";
import { Show } from "solid-js/web";

import { CartManager } from "../cart-manager";
import { CartActions } from "./CartActions";
import { CartEntries } from "./CartEntries";

export const Cart: Component<{
  cartManager: CartManager;
  clearSearch(): void;
}> = (props) => {
  const [refresh, { refetch: refetchCart }] = createResource(
    async () => await props.cartManager.refreshCart()
  );

  const [clearing, setClearing] = createSignal<boolean>(false);
  const clear = async () => {
    setClearing(true);
    props.clearSearch();
    await props.cartManager.clearCart();
    setClearing(false);
  };

  const [removeBadgeId, setRemoveBadgeId] = createSignal<number>();
  const [remove] = createResource(removeBadgeId, async (id) => {
    await props.cartManager.removeBadge(id);
  });

  const anythingLoading = () => refresh.loading || clearing() || remove.loading;
  const canTransfer = () =>
    !anythingLoading() &&
    (props.cartManager.cartEntries()?.result?.length ?? 0) > 0;

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
              <Show when={props.cartManager.pendingTransfers().length > 0}>
                <button
                  class="button is-light is-small"
                  onClick={async (ev) => {
                    ev.preventDefault();

                    const transfer = props.cartManager.getNextTransfer();
                    if (!transfer) return;

                    setClearing(true);
                    await props.cartManager.clearCart();
                    for (let i = 0; i < transfer.length; i += 1) {
                      await props.cartManager.addCartId(transfer[i]);
                    }
                    setClearing(false);
                  }}
                >
                  <span class="icon">
                    <i class="fa-solid fa-satellite-dish"></i>
                  </span>
                </button>
              </Show>

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

              <div
                class="dropdown"
                classList={{ "is-hoverable": canTransfer() }}
              >
                <div class="dropdown-trigger">
                  <button
                    class="button is-link is-small"
                    disabled={!canTransfer()}
                  >
                    <span>Transfer</span>
                    <span class="icon is-small">
                      <i class="fas fa-angle-down"></i>
                    </span>
                  </button>
                </div>
                <div class="dropdown-menu">
                  <div class="dropdown-content">
                    {APIS_CONFIG.terminals.available
                      .filter(
                        (terminal) =>
                          terminal.id !== APIS_CONFIG.terminals.selected
                      )
                      .map((terminal) => (
                        <a
                          href="#"
                          class="dropdown-item"
                          onClick={async (ev) => {
                            ev.preventDefault();
                            setClearing(true);
                            props.clearSearch();
                            await props.cartManager.transfer(terminal.id);
                            setClearing(false);
                          }}
                        >
                          {terminal.name}
                        </a>
                      ))}
                  </div>
                </div>
              </div>

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
          clearSearch={props.clearSearch}
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
