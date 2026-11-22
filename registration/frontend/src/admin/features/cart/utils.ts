import {
  type UndoHistoryReturn,
  createUndoHistory,
} from "@solid-primitives/history";
import type { UseMutationResult } from "@tanstack/solid-query";
import { Big } from "big.js";
import type { Accessor } from "solid-js";

import type {
  BadgeCart,
  BadgePrintResponse,
  CashPaymentOpts,
  CashPaymentResult,
  OnsiteAdminContext,
} from "@admin/api";
import type MqttClient from "@admin/mqtt";
import type { CartStore } from "@admin/providers/cart-provider";

const { format } = new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD",
  trailingZeroDisplay: "stripIfInteger",
});

export const cleanMoneyAmount = (input?: string): string => {
  if (!input || input == "?") return "$0.00";
  if (input.endsWith("%")) return input;

  let multi = 1;
  if (input.startsWith("-")) {
    multi = -1;
    input = input.substring(1);
  }

  if (input.startsWith("$")) {
    input = input.substring(1);
  }

  let parsed: Big;
  try {
    parsed = new Big(input).mul(multi);
  } catch (err) {
    console.error(`Could not parse money ${input}: ${err}`);
    return input;
  }

  return format(parsed.toNumber());
};

export const createAutoPrintCheck = (): ((
  printableIds: number[],
  currentBadges: BadgeCart[],
) => boolean) => {
  let previousBadges: BadgeCart[] = [];

  return function (printableIds: number[], nextBadges: BadgeCart[]): boolean {
    const currentBadges = previousBadges;
    previousBadges = nextBadges;

    if (nextBadges.length === 0 || currentBadges.length !== nextBadges.length) {
      return false;
    }

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
};

export const attemptCashPayment = async (
  applyCashPayment: UseMutationResult<
    CashPaymentResult,
    Error,
    CashPaymentOpts
  >,
  badgeIds: number[],
  total: string,
) => {
  const totalAmount = new Big(total);

  const tendered = prompt("Enter tendered amount");
  if (!tendered) return;

  let tenderedAmount: Big;
  try {
    tenderedAmount = new Big(tendered);
  } catch {
    alert("Invalid amount.");
    return;
  }

  if (tenderedAmount.lt(totalAmount)) {
    alert("Insufficient payment, split tender unsupported.");
    return;
  }

  const result = await applyCashPayment.mutateAsync({ badgeIds, tendered });

  alert(`Change: ${cleanMoneyAmount(result.change)}`);
};

export const printBadgesHelper = async (
  badgeIds: number[],
  printBadges: UseMutationResult<BadgePrintResponse, Error, number[]>,
  mqtt?: MqttClient,
) => {
  await printBadges.mutateAsync(badgeIds, {
    onSuccess: (data) => {
      if (mqtt) {
        const url = new URL(data.file, globalThis.location.href);

        mqtt.publishPrintMessage(
          JSON.stringify({
            url,
          }),
        );
      } else {
        globalThis.open(data.url, "badge");
      }
    },
  });
};

export const getShirtSizeName = (
  config?: OnsiteAdminContext,
  optionValue?: string,
): string | undefined => {
  if (!optionValue) return;

  const sizeName = config?.shirtSizes.find(
    (entry) => entry.id === Number.parseInt(optionValue, 10),
  )?.name;

  return sizeName || optionValue;
};

export const useCartHistory = (
  cartStore: Accessor<CartStore>,
): UndoHistoryReturn => {
  return createUndoHistory(() => {
    const store = cartStore();
    const badgeIds = store.badgeIds();
    return () => store.replace(badgeIds);
  });
};
