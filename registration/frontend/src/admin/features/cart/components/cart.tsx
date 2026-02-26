import {
  faAngleDown,
  faBasketShopping,
  faSatelliteDish,
  faSync,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
import { createShortcut } from "@solid-primitives/keyboard";
import { useQuery } from "@tanstack/solid-query";
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
  fetchCartOptions,
  useAddBadgeToCart,
  useClearCart,
  usePendingTransfers,
  useRemoveBadgeFromCart,
  useTransferCart,
} from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";
import { MqttContext } from "@admin/providers/mqtt-provider";
import { Button } from "@components/button";
import { IconAndLabel } from "@components/icon-and-label";

import { CartActions } from "./cart-actions";
import { CartEntries } from "./cart-entries";

export const Cart: Component<{
  clearSearch(): void;
  setReadyForNext: Setter<boolean>;
}> = (props) => {
  const config = useContext(ConfigContext)!;
  const mqtt = useContext(MqttContext)!;

  const cart = useQuery(fetchCartOptions);

  const clearCart = useClearCart();
  const addBadgeToCart = useAddBadgeToCart();
  const removeBadgeFromCart = useRemoveBadgeFromCart();
  const transferCart = useTransferCart();

  const [pendingTransfers, takeNextTransfer] = usePendingTransfers(mqtt);

  const otherTerminals = createMemo(() =>
    config()?.terminals.available.filter(
      (terminal) => terminal.id !== config()?.terminals.selected?.id,
    ),
  );

  const anythingLoading = () =>
    cart.isFetching ||
    clearCart.isPending ||
    addBadgeToCart.isPending ||
    removeBadgeFromCart.isPending ||
    transferCart.isPending;

  const canTransfer = () =>
    !anythingLoading() && (cart.data?.result.length || 0) > 0;

  createShortcut(["Alt", "R"], () => {
    if (anythingLoading()) return;
    cart.refetch();
  });

  createShortcut(["Alt", "A"], () => {
    if (anythingLoading()) return;
    clearCart.mutate();
  });

  createShortcut(["Alt", "\\"], () => {
    if (anythingLoading()) return;

    const lastBadge = cart.data?.result?.at(-1);
    if (!lastBadge) return;

    removeBadgeFromCart.mutate(lastBadge.id);
  });

  const receiveTransfer = async () => {
    const transfer = takeNextTransfer();
    if (!transfer) return;

    await clearCart.mutateAsync(undefined, {
      onSuccess: async () => {
        for (const entry of transfer) {
          await addBadgeToCart.mutateAsync(entry);
        }
      },
    });
  };

  const performTransfer = (terminal: IdAndName) => {
    props.clearSearch();

    transferCart.mutate(
      {
        terminalId: terminal.id,
        badgeIds: cart.data?.result?.map((badge) => badge.id) || [],
      },
      {
        onSuccess: async () => {
          await clearCart.mutateAsync();
        },
      },
    );
  };

  const addCompletedBadgeToCart = (payload: object | null) => {
    const badgeId =
      payload && "badgeId" in payload && (payload["badgeId"] as number);
    if (badgeId) {
      addBadgeToCart.mutate(badgeId);
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
                  loading={transferCart.isPending}
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
                disabled={anythingLoading()}
                loading={clearCart.isPending}
                title="Alt+A"
                onClick={() => clearCart.mutate()}
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
