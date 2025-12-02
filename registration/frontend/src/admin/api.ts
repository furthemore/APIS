import { QueryClient, queryOptions, useMutation } from "@tanstack/solid-query";
import type Big from "big.js";
import { type Accessor, createEffect, createSignal, onCleanup } from "solid-js";

import { api } from "../queries";
import type MqttClient from "./mqtt";

const KEY_PREFIX = ["onsiteAdmin"];

const BASE_URL = window.location.href;

export type FallibleRequest<T> =
  | {
      success: false;
      reason?: string;
    }
  | ({ success: true } & T);

export type OnsiteAdminContext = {
  user: {
    id: number;
    email: string;
    station?: string;
  };
  mqtt: {
    broker: string;
    auth: {
      user: string;
      token: string;
      base_topic: string;
      print_topic?: string;
    };
  };
  shirtSizes: IdAndName[];
  permissions: Permissions;
  terminals: {
    selected?: SelectedTerminal;
    available: IdAndName[];
  };
};

export type OnsiteAdminSearch = {
  terminal?: number;
};

export type Permissions = {
  cash: boolean;
  cashAdmin: boolean;
  discount: boolean;
};

export type IdAndName = {
  id: number;
  name: string;
};

export type SelectedTerminal = {
  id: number;
  features: {
    printViaMqtt: boolean;
    squareTerminal: boolean;
    paymentType?: "mqtt-app" | "square-terminal";
    cashdrawer: boolean;
  };
};

export type CartResponse = {
  charityDonation: string;
  order_id: number;
  orgDonation: string;
  reference: string;
  subtotal: string;
  total: string;
  total_discount: string;
  result: Badge[];
};

export type Badge = {
  id: number;
  orderId: number;
  abandoned: string;
  age: number;
  badgeName: string;
  badgeNumber?: number;
  firstName: string;
  lastName: string;
  holdType?: string;
  printed: boolean;
  effectiveLevel: EffectiveLevel;
  discount?: Discount;
  level_subtotal: string;
  level_discount: string;
  level_total: string;
  attendee_options: AttendeeOption[];
  reference: string;
  staff?: Staff;
};

export type EffectiveLevel = {
  name: string;
  price: string;
};

export type Discount = {
  name: string;
  amount_off: string;
  percent_off: number;
  reason?: string;
};

export type AttendeeOption = {
  quantity: number;
  item: string;
  price: string;
  total: string;
  reason?: string;
  optionExtraType?: "int" | "bool" | "string" | "ShirtSizes";
  optionValue?: string;
};

export type Staff = {
  shirtSize: string;
};

export type BadgePrintResponse = {
  file: string;
  next: string;
  url: string;
};

export type SearchResults = {
  results: BadgeResult[];
};

export type BadgeResult = {
  id: number;
  editUrl: string;
  attendee: Attendee;
  badgeName: string;
  badgeNumber?: number;
  abandoned: string;
};

export type Attendee = {
  firstName: string;
  lastName: string;
  preferredName?: string;
};

export type TerminalStatus = "open" | "close" | "ready" | "gay" | "blue-light";

export type CashAction = "open" | "deposit" | "safedrop" | "pickup" | "close";

export const urlForBadge = (id: number): URL =>
  new URL(`/admin/registration/badge/${id}/change/`, BASE_URL);

const invalidateCart = async (queryClient: QueryClient) => {
  await queryClient.invalidateQueries({
    queryKey: [...KEY_PREFIX, "cart"],
  });
};

const checkFallibleResponse = <T>(resp: FallibleRequest<T>): T => {
  if (resp.success) {
    return resp;
  } else {
    throw new Error(`API error: ${resp.reason || "unknown"}`);
  }
};

const fetchContext = async (
  id?: number,
  init?: RequestInit,
): Promise<OnsiteAdminContext> => {
  const url = new URL("/registration/onsite/admin/context", BASE_URL);
  if (id) {
    url.searchParams.set("terminal", id.toString());
  }

  return api.get(url, init).json();
};

export const contextQueryOptions = (id?: number) =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "context", { terminal: id }],
    queryFn: ({ signal }) => fetchContext(id, { signal }),
    throwOnError: true,
    staleTime: 1000 * 60 * 5,
  });

const fetchCart = async (init?: RequestInit): Promise<CartResponse> => {
  const url = new URL("/registration/onsite/admin/cart/", BASE_URL);

  return api.get(url, init).json();
};

export const fetchCartOptions = () =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "cart"],
    queryFn: ({ signal }) => fetchCart({ signal }),
    throwOnError: true,
    staleTime: 1000,
  });

const clearBadgePrinted = async (
  id: number,
  init?: RequestInit,
): Promise<FallibleRequest<void>> => {
  const url = new URL(
    "/registration/onsite/admin/badge/print/clear/",
    BASE_URL,
  );
  url.searchParams.set("id", id.toString());

  return api.post(url, init).json();
};

export const useClearBadgePrinted = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "badge", "clearPrinted"],
      mutationFn: async (id: number) => {
        return checkFallibleResponse(await clearBadgePrinted(id));
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
      },
    };
  });

const clearCart = async (): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/admin/clear/", BASE_URL);

  return api.post(url).json();
};

export const useClearCart = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "cart", "clear"],
      mutationFn: async () => {
        return checkFallibleResponse(await clearCart());
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
      },
    };
  });

const addBadgeToCart = (id: number): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/admin/cart/add/", BASE_URL);
  url.searchParams.set("id", id.toString());

  return api.post(url).json();
};

export const useAddBadgeToCart = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "cart", "add"],
      mutationFn: async (id: number) => {
        return checkFallibleResponse(await addBadgeToCart(id));
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
      },
    };
  });

const removeBadgeFromCart = (id: number): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/admin/cart/remove/", BASE_URL);
  url.searchParams.set("id", id.toString());

  return api.post(url).json();
};

export const useRemoveBadgeFromCart = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "cart", "remove"],
      mutationFn: async (id: number) => {
        return checkFallibleResponse(await removeBadgeFromCart(id));
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
      },
    };
  });

const createAndApplyDiscount = (
  amount: string,
): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/admin/discount/create/", BASE_URL);

  const formData = new FormData();
  formData.set("amount", amount);

  return api
    .post(url, {
      body: formData,
    })
    .json();
};

export const useCreateAndApplyDiscount = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "discount", "create"],
      mutationFn: async (amount: string) => {
        return checkFallibleResponse(await createAndApplyDiscount(amount));
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
      },
    };
  });

export type CashPaymentOpts = {
  reference: string;
  total: string;
  tendered: string;
};

const enableCardPayment = (
  fallback: boolean,
): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/admin/payment/", BASE_URL);
  if (fallback) url.searchParams.set("fallback", "true");

  return api.post(url).json();
};

export const useEnableCardPayment = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "payment", "card"],
      mutationFn: async (fallback: boolean) => {
        return checkFallibleResponse(await enableCardPayment(fallback));
      },
    };
  });

const applyCashPayment = ({
  reference,
  total,
  tendered,
}: CashPaymentOpts): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/cash/complete/", BASE_URL);
  url.searchParams.set("reference", reference);
  url.searchParams.set("total", total);
  url.searchParams.set("tendered", tendered);

  return api.post(url).json();
};

export const useApplyCashPayment = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "payment", "cash"],
      mutationFn: async (opts: CashPaymentOpts) => {
        return checkFallibleResponse(await applyCashPayment(opts));
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
      },
    };
  });

const printReceipts = (
  references: string[],
): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/admin/receipt/", BASE_URL);
  references.forEach((reference) =>
    url.searchParams.append("reference", reference),
  );

  return api.post(url).json();
};

export const usePrintReceipts = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "payment", "receipt"],
      mutationFn: async (references: string[]) => {
        return checkFallibleResponse(await printReceipts(references));
      },
    };
  });

const printBadges = async (
  ids: number[],
): Promise<FallibleRequest<BadgePrintResponse>> => {
  const assignUrl = new URL(
    "/registration/onsite/admin/badge/assign/",
    BASE_URL,
  );

  const idObjects = ids.map((id) => {
    return { id };
  });

  const assignmentData = await api
    .post<FallibleRequest<void>>(assignUrl, {
      body: JSON.stringify(idObjects),
    })
    .json();

  if (!assignmentData.success) {
    return { success: false };
  }

  const printUrl = new URL("/registration/onsite/admin/badge/print/", BASE_URL);
  ids.forEach((id) => printUrl.searchParams.append("id", id.toString()));

  const printData = await api
    .post<FallibleRequest<BadgePrintResponse>>(printUrl)
    .json();

  return printData;
};

export const usePrintBadges = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "badge", "print"],
      mutationFn: async (ids: number[]) => {
        return checkFallibleResponse(await printBadges(ids));
      },
    };
  });

export type TransferCartOpts = {
  terminalId: number;
  badgeIds: number[];
};

const transferCart = async ({
  terminalId,
  badgeIds,
}: TransferCartOpts): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/admin/cart/transfer/", BASE_URL);
  url.searchParams.append("terminal_id", terminalId.toString());
  badgeIds.forEach((id) => url.searchParams.append("badge_id", id.toString()));

  return api.post(url).json();
};

export const useTransferCart = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "cart", "transfer"],
      mutationFn: async (opts: TransferCartOpts) => {
        return checkFallibleResponse(await transferCart(opts));
      },
    };
  });

export const usePendingTransfers = (
  mqtt: Accessor<MqttClient | undefined>,
): [Accessor<number[][]>, () => number[] | undefined] => {
  const [pendingTransfers, setPendingTransfers] = createSignal<number[][]>([]);

  const takeNextTransfer = () => {
    const newPendingTransfers = pendingTransfers().slice(0);
    const nextTransfer = newPendingTransfers.shift();
    setPendingTransfers(newPendingTransfers);
    return nextTransfer;
  };

  const addPendingTransfer = (payload: object | null) => {
    if (!payload || !("badgeIds" in payload)) {
      return;
    }

    const newPendingTransfers = pendingTransfers().slice(0);
    newPendingTransfers.push(payload.badgeIds as number[]);
    setPendingTransfers(newPendingTransfers);
  };

  createEffect(() => {
    const m = mqtt();

    m?.emitter.on("transfer", addPendingTransfer);

    onCleanup(() => {
      m?.emitter.off("transfer", addPendingTransfer);
    });
  });

  return [pendingTransfers, takeNextTransfer];
};

const searchAttendees = async (
  query: string,
  init?: RequestInit,
): Promise<FallibleRequest<SearchResults>> => {
  if (query.trim().length === 0) {
    return { success: true, results: [] };
  }

  const url = new URL("/registration/onsite/admin/search/", BASE_URL);
  url.searchParams.set("search", query);

  return api.get(url, init).json();
};

export const searchAttendeesOptions = (query: string) =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "attendee", "search", { query }],
    queryFn: async ({ signal }) => {
      return checkFallibleResponse(await searchAttendees(query, { signal }));
    },
    select: (data) => data.results,
    throwOnError: true,
    staleTime: 1000,
    gcTime: 1000 * 60,
  });

const setTerminalStatus = (
  status: TerminalStatus,
): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/admin/terminal/status/", BASE_URL);
  url.searchParams.set("status", status);

  return api.get(url).json();
};

export const useSetTerminalStatus = () =>
  useMutation(() => {
    return {
      mutationKey: [...KEY_PREFIX, "terminal", "status"],
      mutationFn: async (status: TerminalStatus) => {
        return checkFallibleResponse(await setTerminalStatus(status));
      },
    };
  });

const cashNoSale = (): Promise<FallibleRequest<void>> => {
  const url = new URL("/registration/onsite/cashdrawer/no_sale/", BASE_URL);

  return api.get(url).json();
};

export const useCashNoSale = () =>
  useMutation(() => {
    return {
      mutationKey: [...KEY_PREFIX, "cash", "noSale"],
      mutationFn: async () => {
        return checkFallibleResponse(await cashNoSale());
      },
    };
  });

export type CashAmountActionOpts = {
  action: CashAction;
  amount: Big;
};

const cashAmountAction = ({
  action,
  amount,
}: CashAmountActionOpts): Promise<FallibleRequest<void>> => {
  const url = new URL(`/registration/onsite/cashdrawer/${action}/`, BASE_URL);

  const formData = new FormData();
  formData.set("amount", amount.toString());

  return api.post(url, { body: formData }).json();
};

export const useCashAmountAction = (action: CashAction) =>
  useMutation(() => {
    return {
      mutationKey: [...KEY_PREFIX, "cash", action],
      mutationFn: async (amount: Big) => {
        return checkFallibleResponse(
          await cashAmountAction({ action, amount }),
        );
      },
    };
  });

const CHECKED_BADGE_FIELDS: (keyof BadgeResult & keyof Badge)[] = [
  "abandoned",
  "badgeName",
  "badgeNumber",
];

const getBadgesWithChanges = (
  badgeResults: BadgeResult[],
  cartBadges: Badge[],
): BadgeResult[] => {
  return badgeResults.flatMap((badgeResult) => {
    const cartBadge = cartBadges.find((badge) => badge.id === badgeResult.id);
    if (!cartBadge) return [];

    const hasFieldChanges = CHECKED_BADGE_FIELDS.some(
      (field) => badgeResult[field] !== cartBadge[field],
    );
    if (!hasFieldChanges) return [];

    return [
      {
        ...badgeResult,
        abandoned: cartBadge.abandoned,
        badgeName: cartBadge.badgeName,
        badgeNumber: cartBadge.badgeNumber,
      },
    ];
  });
};

export const updateResultsFromCart = (
  queryClient: QueryClient,
  badges: Badge[],
) => {
  queryClient.setQueriesData(
    { queryKey: [...KEY_PREFIX, "attendee", "search"] },
    (previousData: SearchResults): SearchResults | undefined => {
      const badgesWithChanges = getBadgesWithChanges(
        previousData.results,
        badges,
      );

      if (badgesWithChanges) {
        const results = previousData.results.map((badge) => {
          const change = badgesWithChanges.find(
            (change) => change.id === badge.id,
          );
          return change || badge;
        });

        return {
          results,
        };
      }
    },
  );
};
