import {
  faCreditCard,
  faGift,
  faMoneyBillAlt,
  faPrint,
  faReceipt,
} from "@fortawesome/free-solid-svg-icons";
import { Big } from "big.js";
import {
  type Component,
  type Setter,
  createEffect,
  createMemo,
  createSignal,
  useContext,
} from "solid-js";

import {
  type CartResponse,
  useApplyCashPayment,
  useCreateAndApplyDiscount,
  useEnableCardPayment,
  usePrintBadges,
  usePrintReceipts,
} from "@admin/api";
import type MqttClient from "@admin/mqtt";
import { ConfigContext } from "@admin/providers/config-provider";
import { MqttContext } from "@admin/providers/mqtt-provider";
import { UserSettingsContext } from "@admin/providers/user-settings-provider";
import { IconAndLabel } from "@components/icon-and-label";

import { createAutoClearCheck, createAutoPrintCheck } from "../utils";
import { ActionButton } from "./action-button";

const PRINTABLE_STATUS = new Set(["Paid", "Comp", "Staff", "Dealer"]);

export const CartActions: Component<{
  entries?: CartResponse;
  clearSearch(): void;
  setReadyForNext: Setter<boolean>;
}> = (props) => {
  const config = useContext(ConfigContext)!;
  const userSettings = useContext(UserSettingsContext)!;
  const mqtt = useContext(MqttContext)!;

  const printBadges = usePrintBadges();
  const applyCashPayment = useApplyCashPayment();
  const enableCardPayment = useEnableCardPayment();
  const printReceipts = usePrintReceipts();
  const createAndApplyDiscount = useCreateAndApplyDiscount();

  const [loading, setLoading] = createSignal<boolean>(false);

  const hasHold = createMemo(
    () =>
      props.entries?.result?.some((entry) => !!entry.holdType) ||
      isNaN(parseFloat(props?.entries?.total || "")),
  );

  const allNeedPayment = createMemo(
    () =>
      parseFloat(props.entries?.total || "") > 0 &&
      props.entries?.result.every(
        (entry) => !PRINTABLE_STATUS.has(entry.abandoned),
      ),
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
        ?.map((badge) => badge.id) || [],
  );

  const allBadgesPaid = createMemo(
    () =>
      ((props.entries?.result?.length || 0) > 0 &&
        props.entries?.result?.every((badge) =>
          PRINTABLE_STATUS.has(badge.abandoned),
        )) ||
      false,
  );

  const autoPrintCheck = createAutoPrintCheck();
  createEffect(() => {
    if (
      !config.terminals.selected?.features.printViaMqtt ||
      !userSettings().settings().printAfterPayment
    )
      return;

    if (autoPrintCheck(printableBadgeIds(), props.entries?.result || [])) {
      printBadgesHelper(printableBadgeIds(), printBadges, mqtt());
    }
  });

  const autoClearCheck = createAutoClearCheck();
  createEffect(() => {
    if (!userSettings().settings().clearCartAfterPrint) return;

    if (autoClearCheck(props.entries?.result || [])) {
      props.setReadyForNext(true);
    }
  });

  const hasSquareTerminal = () =>
    config.terminals.selected?.features.squareTerminal;
  const canUseCash = () =>
    config.permissions.cash && config.terminals.selected?.features.cashdrawer;
  const paymentType = () => config.terminals.selected?.features.paymentType;

  const canTenderCash = () =>
    config.permissions.cash && !hasHold() && allNeedPayment();
  const canUseCard = () => !hasHold() && allNeedPayment();
  const hasPrintableBadges = () => printableBadgeIds()?.length > 0 || false;

  const badgeReferences = () =>
    props.entries?.result?.map((badge) => badge.reference) || [];

  return (
    <div>
      <div class="row g-2 mb-2">
        <ActionButton
          class="btn-outline-info"
          disabled={loading() || !hasSquareTerminal() || !allBadgesPaid()}
          setLoading={setLoading}
          action={() => printReceipts.mutateAsync(badgeReferences())}
        >
          <IconAndLabel children="Receipt" icon={faReceipt} fw />
        </ActionButton>

        <ActionButton
          class="btn-primary"
          disabled={loading() || !canUseCash() || !canTenderCash()}
          setLoading={setLoading}
          keyboardShortcut={["Alt", "M"]}
          action={() => {
            if (props.entries) {
              return attemptCashPayment(
                applyCashPayment,
                props.entries.reference,
                props.entries.total,
              );
            }
          }}
        >
          <IconAndLabel children="Cash" icon={faMoneyBillAlt} fw />
        </ActionButton>

        <ActionButton
          class="btn-primary"
          disabled={loading() || !paymentType() || !canUseCard()}
          setLoading={setLoading}
          keyboardShortcut={["Alt", "C"]}
          action={(holdingShift) => enableCardPayment.mutateAsync(holdingShift)}
        >
          <IconAndLabel children="Card" icon={faCreditCard} fw />
        </ActionButton>
      </div>

      <div class="row g-2">
        <ActionButton
          class="btn-outline-warning"
          disabled={loading() || !config.permissions.discount || !canUseCard()}
          setLoading={setLoading}
          action={() => createAndApplyDiscountHelper(createAndApplyDiscount)}
        >
          <IconAndLabel children="Discount" icon={faGift} fw />
        </ActionButton>

        <ActionButton
          class="btn-info"
          disabled={loading() || !hasPrintableBadges()}
          setLoading={setLoading}
          keyboardShortcut={["Control", "P"]}
          action={(holdingShift) => {
            const badgeIds = printableBadgeIds();
            const printViaMqtt =
              config.terminals.selected?.features.printViaMqtt && !holdingShift;

            return printBadgesHelper(
              badgeIds,
              printBadges,
              printViaMqtt ? mqtt() : undefined,
            );
          }}
        >
          <IconAndLabel children="Print Badges" icon={faPrint} fw />
        </ActionButton>
      </div>
    </div>
  );
};

async function attemptCashPayment(
  applyCashPayment: ReturnType<typeof useApplyCashPayment>,
  reference: string,
  total: string,
) {
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

  alert(`Change: $${change.toFixed(2)}`);
}

async function createAndApplyDiscountHelper(
  createAndApplyDiscount: ReturnType<typeof useCreateAndApplyDiscount>,
) {
  const discountAmount = prompt(
    "Enter discount amount, starting with either $ or %",
  );
  if (!discountAmount) return;

  await createAndApplyDiscount.mutateAsync(discountAmount);
}

async function printBadgesHelper(
  badgeIds: number[],
  printBadges: ReturnType<typeof usePrintBadges>,
  mqtt?: MqttClient,
) {
  await printBadges.mutateAsync(badgeIds, {
    onSuccess: async (data) => {
      if (mqtt !== undefined) {
        const url = new URL(data.file, window.location.href);

        mqtt.publishPrintMessage(
          JSON.stringify({
            action: "print",
            url,
          }),
        );
      } else {
        window.open(data.url, "badge");
      }
    },
  });
}
