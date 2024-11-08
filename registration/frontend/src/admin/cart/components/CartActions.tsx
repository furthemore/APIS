import { Component, createMemo, createSignal, useContext } from "solid-js";
import { Big } from "big.js";

import { CartManager, CartResponse } from "../cart-manager";
import { ConfigContext } from "../../providers/config-provider";
import { ActionButton, ActionButtonKey } from "./ActionButton";

const PRINTABLE_STATUS = new Set(["Paid", "Comp", "Staff", "Dealer"]);

export const CartActions: Component<{
  manager: CartManager;
  cartEntries: CartResponse;
}> = (props) => {
  const config = useContext(ConfigContext);

  const [loadingButton, setLoadingButton] = createSignal<ActionButtonKey>();

  const hasHold = createMemo(
    () =>
      props.cartEntries?.result?.some((entry) => !!entry.holdType) ||
      isNaN(parseFloat(props?.cartEntries?.total))
  );

  const needsPayment = createMemo(
    () =>
      parseFloat(props.cartEntries?.total) > 0 &&
      props.cartEntries?.result.some(
        (entry) => !PRINTABLE_STATUS.has(entry.abandoned)
      )
  );

  const printableBadgeIds = createMemo(
    () =>
      props.cartEntries?.result
        ?.filter((badge) => {
          const isPrintable =
            PRINTABLE_STATUS.has(badge.abandoned) &&
            !badge.holdType &&
            !badge.printed;

          return isPrintable;
        })
        ?.map((badge) => badge.id) || []
  );

  const canTenderCash = () =>
    config.permissions.cash && !hasHold() && needsPayment();
  const canUseCard = () => !hasHold() && needsPayment();
  const hasPrintableBadges = () => printableBadgeIds()?.length > 0 || false;

  return (
    <div class="control">
      <div class="columns">
        <ActionButton
          button="cash"
          class="is-primary"
          disabled={!canTenderCash()}
          loadingButton={loadingButton()}
          setLoadingButton={setLoadingButton}
          action={() =>
            attemptCashPayment(
              props.manager,
              props.cartEntries.reference,
              props.cartEntries.total
            )
          }
        >
          <span class="icon">
            <i class="fas fa-money-bill-alt"></i>
          </span>
          <span>Tender Cash</span>
        </ActionButton>
        <ActionButton
          button="card"
          class="is-warning"
          disabled={!canUseCard()}
          loadingButton={loadingButton()}
          setLoadingButton={setLoadingButton}
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
          button="print"
          class="is-primary"
          disabled={!hasPrintableBadges()}
          loadingButton={loadingButton()}
          setLoadingButton={setLoadingButton}
          action={(ev) =>
            printBadges(
              props.manager,
              printableBadgeIds(),
              config.mqtt.supports_printing && !ev.shiftKey
            )
          }
        >
          <span class="icon">
            <i class="fas fa-print"></i>
          </span>
          <span>Print Badges</span>
        </ActionButton>
      </div>
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

  alert(`Change: ${change}`);
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
  mqttPrint: boolean = false
) {
  const resp = await manager.printBadges(ids, mqttPrint);
  if (!resp.success) {
    alert("Error printing badges.");
    return;
  }

  console.debug(`Got response from badge print: mqttPrint=${mqttPrint}, resp=${resp}`);

  if (!mqttPrint) {
    window.open(resp.url, "badge");
  }
}
