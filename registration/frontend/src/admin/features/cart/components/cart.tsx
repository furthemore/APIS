import {
  faAngleDown,
  faBasketShopping,
  faSatelliteDish,
  faSync,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
import { createHotkey } from "@tanstack/solid-hotkeys";
import Fa from "solid-fa";
import {
  type Component,
  For,
  type Setter,
  Show,
  createEffect,
  createMemo,
  onCleanup,
  useContext,
} from "solid-js";

import {
  type IdAndName,
  useCart,
  useExpandBadges,
  usePendingTransfers,
  useTransferCart,
} from "@admin/api";
import { CartContext } from "@admin/providers/cart-provider";
import { ConfigContext } from "@admin/providers/config-provider";
import { MqttContext } from "@admin/providers/mqtt-provider";
import { SelectedTerminalContext } from "@admin/providers/selected-terminal-provider";
import { Button } from "@components/button";
import { IconAndLabel } from "@components/icon-and-label";

import { useCartHistory } from "../utils";
import { CartActions } from "./cart-actions";
import { CartEntries } from "./cart-entries";

export const Cart: Component<{
  clearSearch(): void;
  setReadyForNext: Setter<boolean>;
}> = (props) => {
  const config = useContext(ConfigContext)!;
  const mqtt = useContext(MqttContext)!;
  const cartStore = useContext(CartContext)!;
  const selectedTerminal = useContext(SelectedTerminalContext)!;

  const cart = useCart();

  const expandBadges = useExpandBadges();
  const transferCart = useTransferCart();

  const [pendingTransfers, takeNextTransfer] = usePendingTransfers(mqtt);

  const otherTerminals = createMemo(() =>
    config()?.terminals.available.filter(
      (terminal) => terminal.id !== selectedTerminal().id,
    ),
  );

  const history = useCartHistory(cartStore);

  const anythingLoading = () =>
    cart.isFetching || expandBadges.isPending || transferCart.isPending;

  const canTransfer = () =>
    !anythingLoading() && (cart.data?.result.length || 0) > 0;

  createHotkey("Mod+Z", () => history.undo(), { ignoreInputs: true });

  createHotkey("Alt+R", () => {
    if (anythingLoading()) return;
    cart.refetch();
  });

  createHotkey("Alt+A", () => {
    if (expandBadges.isPending) return;
    cartStore().clear();
  });

  createHotkey("Alt+\\", () => {
    if (expandBadges.isPending) return;

    const lastBadge = cart.data?.result?.at(-1);
    if (!lastBadge) return;

    cartStore().remove(lastBadge.id);
  });

  const receiveTransfer = () => {
    const transfer = takeNextTransfer();
    if (!transfer) return;

    cartStore().replace(transfer);
  };

  const performTransfer = (terminal: IdAndName) => {
    props.clearSearch();

    transferCart.mutate(
      {
        terminalId: terminal.id,
        badgeIds: cartStore().badgeIds(),
      },
      {
        onSuccess: () => {
          cartStore().clear();
        },
      },
    );
  };

  const addCompletedBadgeToCart = (payload: object | null) => {
    const badgeId =
      payload && "badgeId" in payload && (payload["badgeId"] as number);
    if (badgeId) {
      expandBadges.mutate(badgeId);
    }
  };

  createEffect(() => {
    const m = mqtt();

    m?.emitter.on("registration/completed", addCompletedBadgeToCart);

    onCleanup(() => {
      m?.emitter.off("registration/completed", addCompletedBadgeToCart);
    });
  });

  return (
    <div class="card">
      <div class="card-header">
        <div class="row align-items-center">
          <div class="col">
            <h5 class="card-heading mb-0">
              <IconAndLabel children="Cart" icon={faBasketShopping} fw />
            </h5>
          </div>

          <div class="col-auto">
            <div class="d-flex column-gap-1">
              <Show when={pendingTransfers().length > 0}>
                <Button
                  type="button"
                  class="btn btn-sm btn-info"
                  title="Receive Transfer"
                  onClick={receiveTransfer}
                >
                  <Fa icon={faSatelliteDish} fw pulse />
                </Button>
              </Show>

              <Button
                type="button"
                class="btn btn-sm btn-primary"
                title="Alt+R"
                disabled={anythingLoading()}
                loading={cart.isFetching}
                onClick={() => cart.refetch()}
              >
                <Fa icon={faSync} />
              </Button>

              <div class="dropdown">
                <DropdownMenu>
                  <DropdownMenu.Trigger
                    as={Button}
                    type="button"
                    class="btn btn-info btn-sm dropdown-trigger"
                    disabled={!canTransfer() || anythingLoading()}
                  >
                    <IconAndLabel children="Transfer" icon={faAngleDown} fw />
                  </DropdownMenu.Trigger>

                  <DropdownMenu.Portal>
                    <DropdownMenu.Content as="ul" class="dropdown-menu show">
                      <For each={otherTerminals()}>
                        {(terminal) => (
                          <DropdownMenu.Item
                            as="button"
                            type="button"
                            class="dropdown-item"
                            onClick={[performTransfer, terminal]}
                          >
                            {terminal.name}
                          </DropdownMenu.Item>
                        )}
                      </For>
                    </DropdownMenu.Content>
                  </DropdownMenu.Portal>
                </DropdownMenu>
              </div>

              <Button
                class="btn btn-warning btn-sm"
                disabled={expandBadges.isPending || !cart.data?.result.length}
                title="Alt+A"
                onClick={() => cartStore().clear()}
              >
                <IconAndLabel children="Clear" icon={faXmark} fw />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div class="card-body">
        <CartActions
          entries={cart.data}
          clearSearch={props.clearSearch}
          setReadyForNext={props.setReadyForNext}
        />
      </div>

      <Show when={cart.data}>
        <CartEntries entries={cart.data} />
      </Show>
    </div>
  );
};
