import {
  type UndoHistoryReturn,
  createUndoHistory,
} from "@solid-primitives/history";
import { createWritableMemo } from "@solid-primitives/memo";
import type { UseMutationResult } from "@tanstack/solid-query";
import { Big } from "big.js";
import isEqual from "lodash/isEqual";
import { type Accessor, createEffect } from "solid-js";

import type {
  AddBadgeParams,
  BadgeCart,
  BadgePrintResponse,
  CartResponse,
  CashPaymentOpts,
  OnsiteAdminContext,
} from "@admin/api";
import type MqttClient from "@admin/mqtt";

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
  applyCashPayment: UseMutationResult<void, Error, CashPaymentOpts>,
  reference: string,
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

  const change = tenderedAmount.sub(totalAmount);

  await applyCashPayment.mutateAsync({
    reference,
    total,
    tendered,
  });

  alert(`Change: ${cleanMoneyAmount(change.toString())}`);
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
  cart: Accessor<CartResponse | undefined>,
  addBadgeToCart: UseMutationResult<unknown, unknown, AddBadgeParams, unknown>,
): UndoHistoryReturn => {
  const cartBadgeIds = () => cart()?.result.map((badge) => badge.id) || [];

  const [historyCartBadgeIds, setHistoryCartBadgeIds] = createWritableMemo(
    cartBadgeIds,
    [],
    { equals: isEqual },
  );

  createEffect(() => {
    if (!isEqual(cartBadgeIds(), historyCartBadgeIds())) {
      addBadgeToCart.mutate({ ids: historyCartBadgeIds(), assign: true });
    }
  });

  return createUndoHistory(() => {
    const badgeIds = historyCartBadgeIds();
    return () => setHistoryCartBadgeIds(badgeIds);
  });
};
