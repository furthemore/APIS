import { toaster } from "@kobalte/core/toast";
import { createEmitter } from "@solid-primitives/event-bus";
import { useQuery, useQueryClient } from "@tanstack/solid-query";
import {
  type Component,
  type Setter,
  Show,
  Suspense,
  createEffect,
  createSignal,
  lazy,
  onCleanup,
  useContext,
} from "solid-js";

import {
  fetchCartOptions,
  updateResultsFromCart,
  useClearCart,
} from "@admin/api";
import { MqttContext } from "@admin/providers/mqtt-provider";
import { UserSettingsContext } from "@admin/providers/user-settings-provider";
import { ActionToast, type ActionToastType } from "@components/action-toast";
import { ErrorCard } from "@components/error-card";

import { SentryErrorBoundary } from "../../common";
import { AttendeeSearch } from "./attendee-search";
import { Cart } from "./cart";
import { type IdData, Scan } from "./scan";

export type BarcodeEmitter = {
  rawScan: string;
  idCard: IdData;
  url: URL;
};

const BarcodeScanner = lazy(() => import("./scanner"));

const KNOWN_PAYMENT_MESSAGES: Record<string, [string, ActionToastType]> = {
  payment_opened: ["Payment screen opened", "success"],
  payment_cancelled: ["Payment cancelled", "warning"],
  payment_failed: ["Payment failed", "danger"],
  payment_completed: ["Payment completed", "success"],
  registration_opened: ["Registration page opened", "success"],
  registration_completed: ["Registration completed", "success"],
};

const notifyOtherDevice = () => {
  toaster.show((toast) => {
    return (
      <ActionToast
        type="warning"
        message="Another device has connected to this terminal"
        {...toast}
      />
    );
  });
};

const notifyPayment = (payload: object | null) => {
  if (typeof payload !== "string") {
    return;
  }

  const message =
    KNOWN_PAYMENT_MESSAGES[payload as keyof typeof KNOWN_PAYMENT_MESSAGES];
  const [text, type] = (message && [message[0], message[1]]) || [
    payload,
    "is-info",
  ];

  toaster.show((props) => (
    <ActionToast toastId={props.toastId} type={type} message={text} />
  ));
};

export const Onsite: Component<{
  readyForNext: boolean;
  setReadyForNext: Setter<boolean>;
}> = (props) => {
  const userSettings = useContext(UserSettingsContext)!;
  const mqtt = useContext(MqttContext)!;

  const [searchQuery, setSearchQuery] = createSignal<string>("");

  const queryClient = useQueryClient();
  const cart = useQuery(fetchCartOptions);
  const clearCart = useClearCart();

  const refresh = () => cart.refetch();

  const emitter = createEmitter<BarcodeEmitter>();

  createEffect(() => {
    if (props.readyForNext) {
      setSearchQuery("");
      clearCart.mutate(undefined, {
        onSuccess: () => props.setReadyForNext(false),
      });
    }
  });

  createEffect(() => {
    const m = mqtt();

    m?.emitter.on("refresh", refresh);
    m?.emitter.on("presence", notifyOtherDevice);
    m?.emitter.on("notify/payment", notifyPayment);

    onCleanup(() => {
      m?.emitter.off("refresh", refresh);
      m?.emitter.off("presence", notifyOtherDevice);
      m?.emitter.off("notify/payment", notifyPayment);
    });
  });

  createEffect(() => {
    updateResultsFromCart(queryClient, cart.data?.result || []);
  });

  const idsInCart = () => cart.data?.result.map((badge) => badge.id) || [];

  const gotScannedName = (name: string, birthday: string) => {
    const query =
      birthday && userSettings().settings().searchBirthday
        ? `${name} birthday:${birthday}`
        : name;
    setSearchQuery(query);
  };

  return (
    <div class="row my-3">
      <div class="col-md-5 col-xxl-4">
        <SentryErrorBoundary
          fallback={(err, reset) => (
            <ErrorCard
              title="Attendee Search Error"
              err={err}
              reset={() => {
                setSearchQuery("");
                reset();
              }}
            />
          )}
        >
          <AttendeeSearch
            idsInCart={idsInCart()}
            searchQuery={searchQuery()}
            setSearchQuery={setSearchQuery}
          />
        </SentryErrorBoundary>

        <SentryErrorBoundary
          fallback={(err, reset) => (
            <ErrorCard title="Scan Error" err={err} reset={reset} />
          )}
        >
          <Scan
            gotScannedName={gotScannedName}
            emitter={emitter}
            readyForNext={props.readyForNext}
          />

          <Show when={userSettings().settings().usesLocalScanner}>
            <Suspense>
              <BarcodeScanner emitter={emitter} />
            </Suspense>
          </Show>
        </SentryErrorBoundary>
      </div>

      <div class="col">
        <SentryErrorBoundary
          fallback={(err, reset) => (
            <ErrorCard title="Cart Error" err={err} reset={reset} />
          )}
        >
          <Cart
            clearSearch={() => setSearchQuery("")}
            setReadyForNext={props.setReadyForNext}
          />
        </SentryErrorBoundary>
      </div>
    </div>
  );
};
