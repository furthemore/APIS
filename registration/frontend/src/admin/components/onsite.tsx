import { toaster } from "@kobalte/core/toast";
import { useQuery, useQueryClient } from "@tanstack/solid-query";
import {
  type Component,
  type Setter,
  createEffect,
  createSignal,
  onCleanup,
  useContext,
} from "solid-js";

import { ActionToast } from "@components/action-toast";

import { SentryErrorBoundary } from "../../common";
import { ErrorCard } from "../../components/error-card";
import { fetchCartOptions, updateResultsFromCart, useClearCart } from "../api";
import { MqttContext } from "../providers/mqtt-provider";
import { UserSettingsContext } from "../providers/user-settings-provider";
import { AttendeeSearch } from "./attendee-search";
import { Cart } from "./cart";
import { Scan } from "./scan";

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
    m?.emitter.on("admin_presence", notifyOtherDevice);

    onCleanup(() => {
      m?.emitter.off("refresh", refresh);
      m?.emitter.off("admin_presence", notifyOtherDevice);
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
    <>
      <div class="row my-3">
        <div class="col-md-6">
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

          <Scan
            gotScannedName={gotScannedName}
            readyForNext={props.readyForNext}
          />
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
    </>
  );
};
