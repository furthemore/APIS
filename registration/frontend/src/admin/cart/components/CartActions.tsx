import { Component, createEffect, createMemo, useContext } from "solid-js";
import { Big } from "big.js";

import { BadgePrintResponse, CartManager, CartResponse } from "../cart-manager";
import { ConfigContext } from "../../providers/config-provider";
import { publishMessage } from "../../mqtt";

const PRINTABLE_STATUS = new Set(["Paid", "Comp", "Staff", "Dealer"]);

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

    publishMessage("action", JSON.stringify({
      action: "print",
      url,
    }));
  } else {
    window.open(data.url, "badge");
  }
}

export const CartActions: Component<{
  manager: CartManager;
  cartEntries: CartResponse;
}> = (props) => {
  const config = useContext(ConfigContext);

  const hasHold = createMemo(
    () =>
      props.cartEntries?.result?.some((entry) => !!entry.holdType) ||
      isNaN(parseFloat(props?.cartEntries?.total))
  );

  const needsPayment = () => parseFloat(props.cartEntries?.total) > 0;

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

  createEffect(() =>
    console.log(
      `hold: ${hasHold()}, needsPayment: ${needsPayment()}, printable: ${printableBadgeIds()}`
    )
  );

  const canTenderCash = () =>
    config.permissions.cash && !hasHold() && needsPayment();
  const canUseCard = () => !hasHold() && needsPayment();
  const hasPrintableBadges = () => printableBadgeIds()?.length > 0 || false;
  const canApplyDiscount = () => config.permissions.discount && false;

  return (
    <div>
      <div class="row button-group">
        <div class="col-md-6">
          <button
            class="btn btn-block btn-primary"
            disabled={!canTenderCash()}
            onClick={() =>
              attemptCashPayment(
                props.manager,
                props.cartEntries.reference,
                props.cartEntries.total
              )
            }
          >
            <i class="fas fa-money-bill-alt"></i> Tender Cash
          </button>
        </div>
        <div class="col-md-6">
          <button
            class="btn btn-block btn-warning"
            disabled={!canUseCard()}
            onClick={() => enableCardPayment(props.manager)}
          >
            <i class="fas fa-credit-card"></i> Credit/Debit Card
          </button>
        </div>
      </div>
      <div class="row button-group">
        <div class="col-md-6">
          <button
            class="btn btn-block btn-primary"
            disabled={!hasPrintableBadges()}
            onClick={(ev) =>
              printBadges(
                props.manager,
                printableBadgeIds(),
                config.mqtt.supports_printing && !ev.shiftKey,
                config.urls.pdf,
              )
            }
          >
            <i class="fas fa-print"></i> Print Badges
          </button>
        </div>
      </div>
    </div>
  );
};
