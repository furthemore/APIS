import {
  type IconDefinition,
  faBlenderPhone,
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
import { type Component, type Setter, Show } from "solid-js";
import { For } from "solid-js";

import {
  type OnsiteAdminContext,
  useCashAmountAction,
  useCashNoSale,
  useSetTerminalStatus,
} from "@admin/api";

import { amountRequest, mutateThenToast } from "../utils";
import { ActionButton } from "./action-button";

type Action = {
  name: string;
  icon: IconDefinition;
  spin?: boolean;
  keyboardShortcut?: KbdKey[];
  action: () => void;
};

export const Actions: Component<{
  config: OnsiteAdminContext;
  setReadyForNext: Setter<boolean>;
}> = (props) => {
  const setTerminalStatus = useSetTerminalStatus();

  const cashNoSale = useCashNoSale();
  const cashOpen = useCashAmountAction("open");
  const cashDeposit = useCashAmountAction("deposit");
  const cashSafeDrop = useCashAmountAction("safedrop");
  const cashPickup = useCashAmountAction("pickup");
  const cashClose = useCashAmountAction("close");

  const readyForNext = () => props.setReadyForNext(true);

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

  for (const action of standardActions) {
    if (!action.keyboardShortcut) continue;
    createShortcut(action.keyboardShortcut, () => action.action());
  }

  return (
    <DropdownMenu>
      <DropdownMenu.Trigger as="a" class="nav-link dropdown-toggle">
        <Fa icon={faCog} />
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content as="ul" class="dropdown-menu show">
          <For each={standardActions}>
            {(action) => <ActionButton {...action} />}
          </For>

          <Show
            when={
              props.config.permissions.cashAdmin &&
              props.config.terminals.selected?.features?.cashdrawer
            }
          >
            <>
              <li>
                <DropdownMenu.Separator class="dropdown-divider" />
              </li>

              <ActionButton
                name="Open Drawer"
                icon={faMoneyBillWave}
                action={() =>
                  amountRequest(
                    cashOpen,
                    "Enter initial amount in drawer",
                    "Opened cash drawer",
                  )
                }
              />

              <ActionButton
                name="Cash Deposit"
                icon={faPlus}
                action={() =>
                  amountRequest(
                    cashDeposit,
                    "Enter amount added to drawer",
                    "Deposited to cash drawer",
                  )
                }
              />

              <ActionButton
                name="Safe Drop"
                icon={faVault}
                action={() =>
                  amountRequest(
                    cashSafeDrop,
                    "Enter amount dropped into safe",
                    "Added to safe amount",
                  )
                }
              />

              <ActionButton
                name="Cash Pickup"
                icon={faMinus}
                action={() =>
                  amountRequest(
                    cashPickup,
                    "Enter amount picked up from drawer",
                    "Marked as picked up",
                  )
                }
              />

              <ActionButton
                name="Close Drawer"
                icon={faStoreAltSlash}
                action={() =>
                  amountRequest(
                    cashClose,
                    "Enter final amount in drawer",
                    "Closed cash drawer",
                  )
                }
              />

              <ActionButton
                name="No Sale"
                icon={faBlenderPhone}
                spin
                action={() =>
                  mutateThenToast(cashNoSale, undefined, "Marked no sale")
                }
              />
            </>
          </Show>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu>
  );
};
