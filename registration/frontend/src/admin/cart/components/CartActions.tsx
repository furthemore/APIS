import {
  Component,
  createEffect,
  createMemo,
  createSignal,
  JSX,
  Setter,
  useContext,
} from "solid-js";
import { Big } from "big.js";

import { BadgePrintResponse, CartManager, CartResponse } from "../cart-manager";
import { ConfigContext } from "../../providers/config-provider";
import { publishMessage } from "../../mqtt";

const PRINTABLE_STATUS = new Set(["Paid", "Comp", "Staff", "Dealer"]);

type ActionButton = "cash" | "card" | "print";

async function trackLoadingButton<T>(
  setLoadingButton: Setter<ActionButton>,
  button: ActionButton,
  action: Promise<T>
): Promise<T> {
  setLoadingButton(button);
  const resp = await action;
  setLoadingButton(null);
  return resp;
}

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
  mqttPrint: boolean = false,
  pdfUrl: string | null = null
) {
  const resp = await manager.printBadges(ids);
  if (!resp.success) {
    alert("Error printing badges.");
    return;
  }

  // If it was successful, it should always have the correct data.
  const data = resp as BadgePrintResponse;

  if (mqttPrint && pdfUrl && publishMessage) {
    let url = new URL(pdfUrl, window.location.href);
    url.searchParams.append("file", data.file);

    publishMessage(
      "action",
      JSON.stringify({
        action: "print",
        url,
      })
    );
  } else {
    window.open(data.url, "badge");
  }
}

export const CartActions: Component<{
  manager: CartManager;
  cartEntries: CartResponse;
}> = (props) => {
  const config = useContext(ConfigContext);

  const [loadingButton, setLoadingButton] = createSignal<ActionButton | null>();

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
        <LoadableButton
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
          <span class="icon-text">
            <span class="icon">
              <i class="fas fa-money-bill-alt"></i>
            </span>
            <span>Tender Cash</span>
          </span>
        </LoadableButton>
        <LoadableButton
          button="card"
          class="is-warning"
          disabled={!canUseCard()}
          loadingButton={loadingButton()}
          setLoadingButton={setLoadingButton}
          action={() => enableCardPayment(props.manager)}
        >
          <span class="icon-text">
            <span class="icon">
              <i class="fas fa-credit-card"></i>
            </span>
            <span>Credit/Debit Card</span>
          </span>
        </LoadableButton>
      </div>
      <div class="columns">
        <LoadableButton
          button="print"
          class="is-primary"
          disabled={!hasPrintableBadges()}
          loadingButton={loadingButton()}
          setLoadingButton={setLoadingButton}
          action={(ev) =>
            printBadges(
              props.manager,
              printableBadgeIds(),
              config.mqtt.supports_printing && !ev.shiftKey,
              config.urls.pdf
            )
          }
        >
          <span class="icon-text">
            <span class="icon">
              <i class="fas fa-print"></i>
            </span>
            <span>Print Badges</span>
          </span>
        </LoadableButton>
      </div>
    </div>
  );
};

const LoadableButton: Component<{
  button: ActionButton;
  class: string;
  disabled: boolean;
  loadingButton: ActionButton | null;
  setLoadingButton: Setter<ActionButton>;
  action: (ev: MouseEvent) => Promise<void>;
  children: JSX.Element;
}> = (props) => {
  let classes = `button is-fullwidth ${props.class}`;

  return (
    <div class="column">
      <button
        class={classes}
        classList={{ "is-loading": props.loadingButton == props.button }}
        disabled={props.loadingButton != null || props.disabled}
        onClick={(ev) => {
          trackLoadingButton(
            props.setLoadingButton,
            props.button,
            props.action(ev)
          );
        }}
      >
        {props.children}
      </button>
    </div>
  );
};
