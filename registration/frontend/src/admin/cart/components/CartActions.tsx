import {
  Accessor,
  Component,
  createEffect,
  createMemo,
  createSignal,
  Setter,
  useContext,
} from "solid-js";
import { Big } from "big.js";

import { ActionButton } from "./ActionButton";
import { Badge, CartManager, CartResponse } from "../cart-manager";
import { CartActionsError } from "./CartActionsError";
import { ConfigContext } from "../../providers/config-provider";
import { SentryErrorBoundary } from "../../../entrypoints/admin";
import { UserSettingsContext } from "../../providers/user-settings-provider";

const PRINTABLE_STATUS = new Set(["Paid", "Comp", "Staff", "Dealer"]);

export const CartActions: Component<{
  manager: CartManager;
  entries?: CartResponse;
}> = (props) => {
  const config = useContext(ConfigContext)!;
  const userSettings = useContext(UserSettingsContext)!;

  const [loading, setLoading] = createSignal<boolean>(false);

  const hasHold = createMemo(
    () =>
      props.entries?.result?.some((entry) => !!entry.holdType) ||
      isNaN(parseFloat(props?.entries?.total || ""))
  );

  const allNeedPayment = createMemo(
    () =>
      parseFloat(props.entries?.total || "") > 0 &&
      props.entries?.result.every(
        (entry) => !PRINTABLE_STATUS.has(entry.abandoned)
      )
  );

  const printableBadgeIds = createMemo(
    () =>
      props.entries?.result
        ?.filter((badge) => {
          const isPrintable =
            PRINTABLE_STATUS.has(badge.abandoned) &&
            !badge.holdType &&
            !badge.printed;

          return isPrintable;
        })
        ?.map((badge) => badge.id) || []
  );

  if (config.mqtt.supports_printing) {
    const autoPrintCheck = createAutoPrintCheck(printableBadgeIds);

    createEffect(async () => {
      if (!userSettings.userSettings().print_after_payment) return;

      if (autoPrintCheck(props.entries?.result || [])) {
        await printBadges(
          props.manager,
          printableBadgeIds(),
          setLoading,
          userSettings.userSettings().clear_cart_after_print,
          true
        );
      }
    });
  }

  const canTenderCash = () =>
    config.permissions.cash && !hasHold() && allNeedPayment();
  const canUseCard = () => !hasHold() && allNeedPayment();
  const hasPrintableBadges = () => printableBadgeIds()?.length > 0 || false;

  return (
    <div class="control">
      <SentryErrorBoundary
        fallback={(err, reset) => (
          <CartActionsError
            err={err}
            reset={() => {
              setLoading(false);
              reset();
            }}
          />
        )}
      >
        <div class="columns">
          <ActionButton
            class="is-primary"
            disabled={!canTenderCash()}
            loading={loading()}
            setLoading={setLoading}
            keyboardShortcut={["Alt", "M"]}
            action={() => {
              if (props.entries) {
                return attemptCashPayment(
                  props.manager,
                  props.entries.reference,
                  props.entries.total
                );
              }
            }}
          >
            <span class="icon">
              <i class="fas fa-money-bill-alt"></i>
            </span>
            <span>Tender Cash</span>
          </ActionButton>
          <ActionButton
            class="is-warning"
            disabled={!canUseCard()}
            loading={loading()}
            setLoading={setLoading}
            keyboardShortcut={["Alt", "C"]}
            action={() => enableCardPayment(props.manager)}
          >
            <span class="icon">
              <i class="fas fa-credit-card"></i>
            </span>
            <span>Credit/Debit Card</span>
          </ActionButton>
        </div>
        <div class="columns">
          <ActionButton
            class="is-primary"
            disabled={!hasPrintableBadges()}
            loading={loading()}
            setLoading={setLoading}
            keyboardShortcut={["Control", "P"]}
            action={(ev) => {
              let holdingShift = false;
              if (ev instanceof KeyboardEvent || ev instanceof MouseEvent) {
                holdingShift = ev.shiftKey;
              }

              return printBadges(
                props.manager,
                printableBadgeIds(),
                setLoading,
                userSettings.userSettings().clear_cart_after_print,
                config.mqtt.supports_printing && !holdingShift
              );
            }}
          >
            <span class="icon">
              <i class="fas fa-print"></i>
            </span>
            <span>Print Badges</span>
          </ActionButton>
        </div>
      </SentryErrorBoundary>
    </div>
  );
};

async function attemptCashPayment(
  manager: CartManager,
  reference: string,
  total: string
) {
  const totalAmount = new Big(total);

  const tendered = prompt("Enter tendered amount");
  if (!tendered) return;

  let tenderedAmount: Big;
  try {
    tenderedAmount = new Big(tendered);
  } catch (err) {
    alert("Invalid amount.");
    return;
  }

  if (tenderedAmount.lt(totalAmount)) {
    alert("Insufficient payment, split tender unsupported.");
    return;
  }

  let change = tenderedAmount.sub(totalAmount);

  const resp = await manager.applyCashPayment(reference, total, tendered);
  if (resp.success) {
    manager.refreshCart();
  } else {
    alert("Error posting cash transaction.");
    return;
  }

  alert(`Change: $${change.toFixed(2)}`);
}

async function enableCardPayment(manager: CartManager) {
  const resp = await manager.enableCardPayment();
  if (!resp.success) {
    alert("Error enabling card payment.");
  }
}

async function printBadges(
  manager: CartManager,
  ids: number[],
  setLoading: Setter<boolean>,
  clearCart: boolean,
  mqttPrint: boolean
) {
  setLoading(true);
  const resp = await manager.printBadges(ids, clearCart, mqttPrint);
  setLoading(false);

  if (!resp.success) {
    alert("Error printing badges.");
    return;
  }

  if (!mqttPrint) {
    window.open(resp.url, "badge");
  }
}

function createAutoPrintCheck(
  printableBadgeIds: Accessor<number[]>
): (currentBadges: Badge[]) => boolean {
  let previousBadges: Badge[] = [];

  return function (nextBadges: Badge[]): boolean {
    let currentBadges = previousBadges;
    previousBadges = nextBadges;

    if (nextBadges.length === 0 || currentBadges.length !== nextBadges.length) {
      return false;
    }

    const printableIds = printableBadgeIds();

    for (let i = 0; i < currentBadges.length; i += 1) {
      const prev = currentBadges[i];
      const curr = nextBadges[i];

      if (!printableIds.includes(curr.id)) {
        return false;
      }

      if (
        prev.id !== curr.id ||
        curr.abandoned === prev.abandoned ||
        curr.abandoned !== "Paid"
      ) {
        return false;
      }
    }

    return true;
  };
}
