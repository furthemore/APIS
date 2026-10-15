import {
  QueryClient,
  queryOptions,
  useMutation,
  useQuery,
} from "@tanstack/solid-query";
import type Big from "big.js";
import type { AfterResponseHook, BeforeRequestHook } from "ky";
import {
  type Accessor,
  createEffect,
  createSignal,
  onCleanup,
  useContext,
} from "solid-js";

import { api as baseApi } from "../queries";
import type MqttClient from "./mqtt";
import { CartContext } from "./providers/cart-provider";

const KEY_PREFIX = ["onsiteAdmin"];

export const TERMINAL_SEARCH_PARAM = "terminal";

const redirectOnLoginResponse: AfterResponseHook = ({
  response,
}: {
  response: Response;
}) => {
  if (response.redirected && response.url.includes("/accounts/login")) {
    const url = new URL(response.url);
    url.searchParams.set(
      "next",
      globalThis.location.pathname + globalThis.location.search,
    );

    globalThis.location.href = url.toString();
  }
};

const injectTerminal: BeforeRequestHook = ({ request }) => {
  const raw = new URLSearchParams(globalThis.location.search).get(
    TERMINAL_SEARCH_PARAM,
  );
  if (!raw) return;

  const terminalId = Number(raw);
  if (Number.isSafeInteger(terminalId) && terminalId > 0) {
    request.headers.set("X-Terminal-Id", terminalId.toString());
  }
};

const adminApi = baseApi.extend({
  hooks: {
    beforeRequest: [injectTerminal],
    afterResponse: [redirectOnLoginResponse],
  },
});

export type FallibleRequest<T> =
  | {
      success: false;
      reason?: string;
    }
  | ({ success: true } & T);

export type Terminals = {
  terminals: TerminalDetail[];
};

export type PaymentType = "mqtt-app" | "square-terminal";

export type TerminalDetail = {
  id: number;
  name: string;
  cashdrawer: boolean;
  printViaMqtt?: string;
  paymentType?: PaymentType;
  backgroundColor: string;
  foregroundColor: string;
  squareTerminal: boolean;
};

export type OnsiteAdminContext = {
  user: {
    id: number;
    email: string;
  };
  mqtt?: {
    broker: string;
    auth: {
      user: string;
      token: string;
      root_topic: string;
      print_topic?: string;
    };
  };
  shirtSizes: IdAndName[];
  departments: IdAndName[];
  events: IdAndName[];
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
    card: boolean;
    cashdrawer: boolean;
    prompt: boolean;
    squareTerminal: boolean;
  };
};

export type BadgeState =
  "Staff" | "Dealer" | "Paid" | "Unpaid" | "Comp" | "Abandoned";

export type Badge = {
  id: number;
  abandoned: BadgeState;
  badgeName: string;
  badgeNumber?: number;
};

export type CartResponse = {
  badge_ids: number[];
  charityDonation: string;
  order_id: number | null;
  orgDonation: string;
  reference: string | null;
  subtotal: string;
  total: string;
  total_discount: string;
  result: BadgeCart[];
};

export type BadgeCart = Badge & {
  orderId: number;
  eventId: number;
  age: number;
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
  id: number;
  quantity: number;
  item: string;
  price: string;
  total: string;
  reason?: string;
  optionExtraType?: "int" | "bool" | "string" | "ShirtSizes";
  optionValue?: string;
  requiresFulfillment: boolean;
  fulfilledAt?: string;
};

export type Staff = {
  shirtSize: string;
  beforeDeadline: boolean;
};

export type BadgePrintResponse = {
  file: string;
  next: string;
  url: string;
};

export type SearchResults = {
  results: BadgeResult[];
};

export type BadgeResult = Badge & {
  editUrl: string;
  attendee: Attendee;
};

export type Attendee = {
  firstName: string;
  lastName: string;
  preferredName?: string;
};

export type DrawerStatus = {
  status: "CLOSED" | "SHORT" | "OPEN";
  total: string;
};

export type TerminalStatus = "open" | "close" | "ready" | "gay" | "blue-light";

export type CashAction = "open" | "deposit" | "safedrop" | "pickup" | "close";

export type AttendeeDetails = {
  firstName?: string;
  lastName?: string;
  preferredName?: string;
  email?: string;
  phone?: string;
  address1?: string;
  address2?: string;
  city?: string;
  state?: string;
  country?: string;
  postalCode?: string;
  dob?: string;
};

export const urlForBadge = (id: number): URL =>
  new URL(`/admin/registration/badge/${id}/change/`, globalThis.location.href);

export const urlForOnsiteDetails = (details: AttendeeDetails): URL => {
  const regUrl = new URL("/registration/onsite", globalThis.location.href);
  Object.entries(details).forEach(([name, value]) => {
    regUrl.searchParams.set(name, value);
  });
  return regUrl;
};

const invalidateCart = async (queryClient: QueryClient) => {
  await queryClient.invalidateQueries({
    queryKey: [...KEY_PREFIX, "cart"],
  });
};

export class APIError extends Error {
  reason?: string;

  constructor(reason?: string) {
    super(`API error: ${reason || "unknown"}`);
    this.name = this.constructor.name;
    this.reason = reason;
  }
}

const checkFallibleResponse = <T>(resp: FallibleRequest<T>): T => {
  if (resp.success) {
    return resp;
  } else {
    throw new APIError(resp.reason);
  }
};

const fetchTerminals = async (init?: RequestInit): Promise<Terminals> => {
  return adminApi.get("registration/onsite/admin/terminals", init).json();
};

export const terminalQueryOptions = () =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "terminals"],
    queryFn: ({ signal }) => fetchTerminals({ signal }),
    throwOnError: true,
    staleTime: Infinity,
  });

const fetchContext = async (
  id?: number,
  init?: RequestInit,
): Promise<OnsiteAdminContext> => {
  return adminApi
    .get("registration/onsite/admin/context", {
      ...init,
      searchParams: { terminal: id },
    })
    .json();
};

export const contextQueryOptions = (id?: number) =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "context", { terminal: id }],
    queryFn: ({ signal }) => fetchContext(id, { signal }),
    throwOnError: true,
    staleTime: 1000 * 60 * 60 * 24,
    enabled: !!id,
  });

const ping = async (init?: RequestInit): Promise<FallibleRequest<void>> => {
  return adminApi.get("registration/onsite/admin/ping", init).json();
};

export const useSessionKeepalive = () =>
  useQuery(() => ({
    queryKey: [...KEY_PREFIX, "ping"],
    queryFn: ({ signal }) => ping({ signal }),
    refetchInterval: 1000 * 60 * 10,
    staleTime: 0,
    retry: false,
  }));

const fetchCart = async (
  badgeIds: number[],
  init?: RequestInit,
): Promise<CartResponse> => {
  const searchParams = new URLSearchParams();
  for (const id of badgeIds) {
    searchParams.append("id", id.toString());
  }

  return adminApi
    .get("registration/onsite/admin/cart", { ...init, searchParams })
    .json();
};

const fetchCartOptions = (badgeIds: number[]) =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "cart", badgeIds],
    queryFn: ({ signal }) => fetchCart(badgeIds, { signal }),
    throwOnError: true,
    staleTime: 1000,
  });

export const useCart = () => {
  const cart = useContext(CartContext)!;

  return useQuery(() => fetchCartOptions(cart().badgeIds()));
};

export const useCartSync = () => {
  const cart = useContext(CartContext)!;
  const query = useCart();

  createEffect(() => {
    const ids = query.data?.badge_ids;
    if (ids) cart().replace(ids);
  });

  return query;
};

const expandBadges = async (badgeIds: number[]): Promise<number[]> => {
  const searchParams = new URLSearchParams();
  for (const id of badgeIds) {
    searchParams.append("id", id.toString());
  }

  const resp = await adminApi
    .get<FallibleRequest<{ badge_ids: number[] }>>(
      "registration/onsite/admin/cart/expand",
      { searchParams },
    )
    .json();

  return checkFallibleResponse(resp).badge_ids;
};

export const useExpandBadges = () => {
  const cart = useContext(CartContext)!;

  return useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "cart", "expand"],
      mutationFn: async (params: number | number[]) => {
        const ids = typeof params === "number" ? [params] : params;
        const expanded = await expandBadges(ids);
        cart().add(expanded);
        return expanded;
      },
    };
  });
};

const clearBadgePrinted = async (
  id: number,
  init?: RequestInit,
): Promise<FallibleRequest<void>> => {
  return adminApi
    .post("registration/onsite/admin/badge/print/clear", {
      ...init,
      searchParams: { id },
    })
    .json();
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

export type DiscountParams = {
  type: "Amount" | "Percent";
  department: number;
  value: string;
  notes: string;
  badgeIds: number[];
};

const createAndApplyDiscount = (
  params: DiscountParams,
): Promise<FallibleRequest<void>> => {
  return adminApi
    .post("registration/onsite/admin/discount/create", {
      json: {
        type: params.type,
        department: params.department,
        value: params.value,
        notes: params.notes,
        badge_ids: params.badgeIds,
      },
    })
    .json();
};

export const useCreateAndApplyDiscount = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "discount", "create"],
      mutationFn: async (params: DiscountParams) => {
        return checkFallibleResponse(await createAndApplyDiscount(params));
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
      },
    };
  });

export type CashPaymentOpts = {
  badgeIds: number[];
  tendered: string;
};

export type CashPaymentResult = {
  total: string;
  change: string;
};

export type EnableCardPaymentOpts = {
  badgeIds: number[];
  fallback: boolean;
};

const enableCardPayment = (
  opts: EnableCardPaymentOpts,
): Promise<FallibleRequest<void>> => {
  return adminApi
    .post("registration/onsite/admin/payment", {
      json: { badge_ids: opts.badgeIds },
      searchParams: opts.fallback ? { fallback: "true" } : undefined,
    })
    .json();
};

export const useEnableCardPayment = () =>
  useMutation(() => {
    return {
      throwOnError: true,
      mutationKey: [...KEY_PREFIX, "payment", "card"],
      mutationFn: async (opts: EnableCardPaymentOpts) => {
        return checkFallibleResponse(await enableCardPayment(opts));
      },
    };
  });

const applyCashPayment = (
  opts: CashPaymentOpts,
): Promise<FallibleRequest<CashPaymentResult>> => {
  return adminApi
    .post("registration/onsite/cash/complete", {
      json: { badge_ids: opts.badgeIds, tendered: opts.tendered },
    })
    .json();
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
  const searchParams = new URLSearchParams();
  for (const reference of references) {
    searchParams.append("reference", reference);
  }

  return adminApi
    .post("registration/onsite/admin/receipt", { searchParams })
    .json();
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
  const idObjects = ids.map((id) => {
    return { id };
  });

  const assignmentData = await adminApi
    .post<FallibleRequest<void>>("registration/onsite/admin/badge/assign", {
      body: JSON.stringify(idObjects),
    })
    .json();

  if (!assignmentData.success) {
    return { success: false, reason: assignmentData.reason };
  }

  const searchParams = new URLSearchParams();
  for (const id of ids) {
    searchParams.append("id", id.toString());
  }

  const printData = await adminApi
    .post<FallibleRequest<BadgePrintResponse>>(
      "registration/onsite/admin/badge/print",
      { searchParams },
    )
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
  const searchParams = [
    ["terminal_id", terminalId],
    ...badgeIds.map((badgeId) => ["badge_id", badgeId]),
  ];

  return adminApi
    .post("registration/onsite/admin/cart/transfer", { searchParams })
    .json();
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

  return adminApi
    .get("registration/onsite/admin/search", {
      ...init,
      searchParams: { search: query },
    })
    .json();
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

const cashStatus = (
  init?: RequestInit,
): Promise<FallibleRequest<DrawerStatus>> => {
  return adminApi.get("registration/onsite/cashdrawer/status", init).json();
};

export const cashStatusOptions = (enabled: boolean) =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "cash", "status"],
    queryFn: async ({ signal }) => {
      return checkFallibleResponse(await cashStatus({ signal }));
    },
    throwOnError: true,
    enabled,
  });

const cashNoSale = (): Promise<FallibleRequest<void>> => {
  return adminApi.post("registration/onsite/cashdrawer/no-sale").json();
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
  const formData = new FormData();
  formData.set("amount", amount.toString());

  return adminApi
    .post(`registration/onsite/cashdrawer/${action}`, {
      body: formData,
    })
    .json();
};

export const useCashAmountAction = (action: CashAction) =>
  useMutation(() => {
    return {
      mutationKey: [...KEY_PREFIX, "cash", action],
      mutationFn: async (amount: Big) => {
        return checkFallibleResponse(await cashAmountAction({ action, amount }));
      },
    };
  });

const CHECKED_BADGE_FIELDS: (keyof Badge)[] = [
  "abandoned",
  "badgeName",
  "badgeNumber",
];

const getBadgesWithChanges = (
  badgeResults: BadgeResult[],
  cartBadges: BadgeCart[],
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
  badges: BadgeCart[],
) => {
  queryClient.setQueriesData(
    { queryKey: [...KEY_PREFIX, "attendee", "search"] },
    (previousData: SearchResults | undefined): SearchResults | undefined => {
      if (!previousData) return;

      const badgesWithChanges = getBadgesWithChanges(
        previousData.results,
        badges,
      );

      if (badgesWithChanges.length > 0) {
        const results = previousData.results.map((badge) => {
          const change = badgesWithChanges.find(
            (change) => change.id === badge.id,
          );
          return change ?? badge;
        });

        return {
          results,
        };
      }
    },
  );
};

const attendeeDetails = (
  badgeId: number,
  init?: RequestInit,
): Promise<FallibleRequest<{ attendee: AttendeeDetails }>> => {
  return adminApi
    .get("registration/onsite/admin/attendee", {
      ...init,
      searchParams: { id: badgeId },
    })
    .json();
};

export const attendeeDetailsOptions = (badgeId: number) =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "attendee", badgeId],
    queryFn: async ({ signal }) => {
      return checkFallibleResponse(await attendeeDetails(badgeId, { signal }));
    },
    staleTime: 1000 * 10,
    refetchOnWindowFocus: false,
    throwOnError: true,
  });

const getToken = (): Promise<FallibleRequest<{ token: string }>> => {
  return adminApi.post("registration/onsite/admin/regtoken").json();
};

export const useGetToken = () =>
  useMutation(() => {
    return {
      mutationKey: [...KEY_PREFIX, "token"],
      mutationFn: async () => {
        return checkFallibleResponse(await getToken());
      },
    };
  });

const fulfillOption = (id: number): Promise<FallibleRequest<void>> => {
  const formData = new FormData();
  formData.set("id", id.toString());

  return adminApi
    .post("registration/onsite/admin/fulfill", { body: formData })
    .json();
};

export const useFulfillOption = () =>
  useMutation(() => {
    return {
      mutationKey: [...KEY_PREFIX, "fulfill"],
      mutationFn: async (id: number) => {
        return checkFallibleResponse(await fulfillOption(id));
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
      },
    };
  });

export type BadgeEditParams = {
  id: number;
  badgeName: string;
  eventId: number;
};

const editBadge = (params: BadgeEditParams): Promise<FallibleRequest<void>> => {
  const searchParams = new URLSearchParams();
  searchParams.set("id", params.id.toString());
  searchParams.set("badge_name", params.badgeName);
  searchParams.set("event_id", params.eventId.toString());

  return adminApi
    .post("registration/onsite/admin/badge/edit", { searchParams })
    .json();
};

export type PrintHistoryEntry = {
  source: string;
  terminal?: string;
  printedAt: string;
};

export type RollForwardEntry = {
  fromEvent: string;
  toEvent: string;
  rolledAt: string;
  rolledBy?: string;
};

const fetchBadgeHistory = (
  badgeId: number,
  init?: RequestInit,
): Promise<
  FallibleRequest<{
    printHistory: PrintHistoryEntry[];
    rollHistory: RollForwardEntry[];
  }>
> =>
  adminApi
    .get("registration/onsite/admin/badge/history", {
      ...init,
      searchParams: { id: badgeId },
    })
    .json();

export const badgeHistoryOptions = (badgeId: number) =>
  queryOptions({
    queryKey: [...KEY_PREFIX, "badge", badgeId, "history"],
    queryFn: async ({ signal }) =>
      checkFallibleResponse(await fetchBadgeHistory(badgeId, { signal })),
    throwOnError: true,
  });

export const useEditBadge = () =>
  useMutation(() => {
    return {
      mutationKey: [...KEY_PREFIX, "badge", "edit"],
      mutationFn: async (params: BadgeEditParams) => {
        return checkFallibleResponse(await editBadge(params));
      },
      onSuccess: async (_data, _variables, _result, context) => {
        await invalidateCart(context.client);
        await context.client.invalidateQueries({
          queryKey: [...KEY_PREFIX, "attendee", "search"],
        });
      },
    };
  });
