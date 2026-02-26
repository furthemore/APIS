import {
  faCreditCard,
  faGift,
  faMoneyBillAlt,
  faPrint,
  faReceipt,
} from "@fortawesome/free-solid-svg-icons";
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
import { ConfigContext } from "@admin/providers/config-provider";
import { MqttContext } from "@admin/providers/mqtt-provider";
import { UserSettingsContext } from "@admin/providers/user-settings-provider";
import { IconAndLabel } from "@components/icon-and-label";

import {
  attemptCashPayment,
  createAndApplyDiscountHelper,
  createAutoClearCheck,
  createAutoPrintCheck,
  printBadgesHelper,
} from "../utils";
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
      Number.isNaN(Number.parseFloat(props?.entries?.total || "")),
  );

  const allNeedPayment = createMemo(
    () =>
      Number.parseFloat(props.entries?.total || "") > 0 &&
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
      !config()?.mqtt?.auth.print_topic ||
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
    config()?.terminals.selected?.features.squareTerminal;
  const terminalHandlesCash = () =>
    config()?.permissions.cash &&
    config()?.terminals.selected?.features.cashdrawer;

  const canApplyPayment = () => !hasHold() && allNeedPayment();
  const hasPrintableBadges = () => printableBadgeIds()?.length > 0 || false;
  const supportsCard = () => config()?.terminals?.selected?.features.card;

  const badgeReferences = () =>
    props.entries?.result?.map((badge) => badge.reference) || [];

  return (
    <div>
      <div class="row g-2 mb-2">
        <ActionButton
          class="btn-outline-warning"
          disabled={
            loading() || !config()?.permissions.discount || !canApplyPayment()
          }
          setLoading={setLoading}
          action={() => createAndApplyDiscountHelper(createAndApplyDiscount)}
        >
          <IconAndLabel children="Discount" icon={faGift} fw />
        </ActionButton>

        <ActionButton
          class="btn-primary"
          disabled={loading() || !terminalHandlesCash() || !canApplyPayment()}
          setLoading={setLoading}
          keyboardShortcut={"Alt+M"}
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
          disabled={loading() || !supportsCard() || !canApplyPayment()}
          setLoading={setLoading}
          keyboardShortcut={"Alt+C"}
          action={(holdingShift) => enableCardPayment.mutateAsync(holdingShift)}
        >
          <IconAndLabel children="Card" icon={faCreditCard} fw />
        </ActionButton>
      </div>

      <div class="row g-2">
        <ActionButton
          class="btn-outline-info"
          disabled={loading() || !hasSquareTerminal() || !allBadgesPaid()}
          setLoading={setLoading}
          action={() => printReceipts.mutateAsync(badgeReferences())}
        >
          <IconAndLabel children="Receipt" icon={faReceipt} fw />
        </ActionButton>

        <ActionButton
          class="btn-info"
          disabled={loading() || !hasPrintableBadges()}
          setLoading={setLoading}
          keyboardShortcut={"Mod+P"}
          action={(holdingShift) => {
            const badgeIds = printableBadgeIds();
            const printViaMqtt =
              config()?.mqtt?.auth.print_topic && !holdingShift;

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
