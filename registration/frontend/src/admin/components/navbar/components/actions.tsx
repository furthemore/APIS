import {
  type IconDefinition,
  faBlenderPhone,
  faCashRegister,
  faCheck,
  faCog,
  faForward,
  faK,
  faMinus,
  faMoneyBillWave,
  faPlus,
  faRainbow,
  faStoreAltSlash,
  faVault,
  faWindowClose,
} from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
import { type KbdKey, createShortcut } from "@solid-primitives/keyboard";
import Fa from "solid-fa";
import {
  type Component,
  type Setter,
  Show,
  createSignal,
  useContext,
} from "solid-js";
import { For } from "solid-js";

import {
  useCashAmountAction,
  useCashNoSale,
  useSetTerminalStatus,
} from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";
import { IconAndLabel } from "@components/icon-and-label";

import { amountRequest, mutateThenToast } from "../utils";
import { ActionButton } from "./action-button";
import { CashdrawerStatus } from "./cashdrawer-status";

type Action = {
  name: string;
  icon: IconDefinition;
  spin?: boolean;
  keyboardShortcut?: KbdKey[];
  action: () => void;
};

export const Actions: Component<{
  setReadyForNext: Setter<boolean>;
}> = (props) => {
  const config = useContext(ConfigContext)!;

  const [showCashStatus, setShowCashStatus] = createSignal(false);

  const setTerminalStatus = useSetTerminalStatus();

  const cashNoSale = useCashNoSale();
  const cashOpen = useCashAmountAction("open");
  const cashDeposit = useCashAmountAction("deposit");
  const cashSafeDrop = useCashAmountAction("safedrop");
  const cashPickup = useCashAmountAction("pickup");
  const cashClose = useCashAmountAction("close");

  const readyForNext = () => props.setReadyForNext(true);

  const showCashActions = () =>
    config()?.permissions.cashAdmin &&
    config()?.terminals.selected?.features.cashdrawer;

  const standardActions: Action[] = [
    {
      name: "Open Position",
      icon: faCheck,
      keyboardShortcut: ["Alt", "O"],
      action: () =>
        mutateThenToast(setTerminalStatus, "open", "Marked terminal as open"),
    },
    {
      name: "Close Position",
      icon: faWindowClose,
      keyboardShortcut: ["Alt", "L"],
      action: () =>
        mutateThenToast(setTerminalStatus, "close", "Mark terminal as closed"),
    },
    {
      name: "Next Customer",
      icon: faForward,
      keyboardShortcut: ["Alt", "N"],
      action: () =>
        mutateThenToast(
          setTerminalStatus,
          "ready",
          "Marked terminal as ready for next",
          readyForNext,
        ),
    },
    {
      name: "Party Mode",
      icon: faRainbow,
      keyboardShortcut: ["Alt", "K"],
      action: () => mutateThenToast(setTerminalStatus, "gay", "🌈🏳️‍🌈🏳️‍⚧️"),
    },
    {
      name: "Blue Light Special",
      icon: faK,
      keyboardShortcut: ["Alt", "K"],
      action: () => mutateThenToast(setTerminalStatus, "blue-light", "🟦"),
    },
  ];

  const cashActions: Action[] = [
    {
      name: "Open Drawer",
      icon: faMoneyBillWave,
      action: () =>
        amountRequest(
          cashOpen,
          "Enter initial amount in drawer",
          "Opened cash drawer",
        ),
    },
    {
      name: "Cash Deposit",
      icon: faPlus,
      action: () =>
        amountRequest(
          cashDeposit,
          "Enter amount added to drawer",
          "Deposited to cash drawer",
        ),
    },
    {
      name: "Safe Drop",
      icon: faVault,
      action: () =>
        amountRequest(
          cashSafeDrop,
          "Enter amount dropped into safe",
          "Added to safe amount",
        ),
    },
    {
      name: "Cash Pickup",
      icon: faMinus,
      action: () =>
        amountRequest(
          cashPickup,
          "Enter amount picked up from drawer",
          "Marked as picked up",
        ),
    },
    {
      name: "Close Drawer",
      icon: faStoreAltSlash,
      action: () =>
        amountRequest(
          cashClose,
          "Enter final amount in drawer",
          "Closed cash drawer",
        ),
    },
    {
      name: "No Sale",
      icon: faBlenderPhone,
      spin: true,
      action: () => mutateThenToast(cashNoSale, undefined, "Marked no sale"),
    },
  ];

  for (const action of standardActions) {
    if (!action.keyboardShortcut) continue;
    createShortcut(action.keyboardShortcut, () => action.action());
  }

  return (
    <>
      <CashdrawerStatus signal={[showCashStatus, setShowCashStatus]} />

      <DropdownMenu>
        <DropdownMenu.Trigger as="button" class="nav-link dropdown-toggle">
          <Fa icon={faCog} />
        </DropdownMenu.Trigger>

        <DropdownMenu.Portal>
          <DropdownMenu.Content as="ul" class="dropdown-menu show">
            <For each={standardActions}>
              {(action) => <ActionButton {...action} />}
            </For>

            <Show when={showCashActions()}>
              <>
                <li>
                  <DropdownMenu.Separator class="dropdown-divider" />
                </li>

                <DropdownMenu.Item as="li">
                  <button
                    class="dropdown-item"
                    onClick={() => setShowCashStatus(true)}
                  >
                    <IconAndLabel
                      children="Cashdrawer Status"
                      icon={faCashRegister}
                      fw
                    />
                  </button>
                </DropdownMenu.Item>

                <For each={cashActions}>
                  {(action) => <ActionButton {...action} />}
                </For>
              </>
            </Show>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu>
    </>
  );
};
