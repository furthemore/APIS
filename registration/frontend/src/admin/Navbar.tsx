import { Dialog } from "@kobalte/core/dialog";
import { KbdKey, createShortcut } from "@solid-primitives/keyboard";
import { Big } from "big.js";
import {
  Component,
  For,
  Setter,
  Show,
  createEffect,
  createSignal,
  useContext,
} from "solid-js";

import { ApisConfig, CSRF_TOKEN } from "../entrypoints/admin";
import { FallibleRequest, api } from "./api";
import { CartManager } from "./cart";
import { ConfigContext } from "./providers/config-provider";
import {
  UserSettingKey,
  UserSettingsContext,
  UserSettingsManager,
} from "./providers/user-settings-provider";

const KNOWN_SHORTCUTS = [
  { shortcut: "Alt+O", description: "Open position" },
  { shortcut: "Alt+L", description: "Close position" },
  { shortcut: "Alt+N", description: "Ready for next" },
  { shortcut: "Ctrl+E", description: "Create new attendee" },
  { shortcut: "Ctrl+M", description: "Create new attendee from scanned ID" },
  { shortcut: "Alt+F", description: "Clear results and focus search field" },
  {
    shortcut: "↓",
    description: "While searching, move selection one result down",
  },
  {
    shortcut: "↑",
    description: "While searching, move selection one result up",
  },
  {
    shortcut: "Alt+.",
    description: "Add first eligible or selected search result to cart",
  },
  {
    shortcut: "Alt+E",
    description: "Edit the currently selected search result",
  },
  { shortcut: "Alt+D", description: "Scroll to show all scanner entries" },
  { shortcut: "Alt+S", description: "Clear scanner entries" },
  { shortcut: "Alt+A", description: "Clear cart" },
  { shortcut: "Alt+R", description: "Reload cart" },
  { shortcut: "Alt+\\", description: "Remove last badge from cart" },
  { shortcut: "Alt+M", description: "Tender cash payment" },
  { shortcut: "Alt+C", description: "Prompt for card payment" },
  { shortcut: "Ctrl+P", description: "Print badges in cart" },
];

const ActionButton: Component<{
  name: string;
  icon: string;
  action: () => any;
  keyboardShortcut?: KbdKey[];
}> = (props) => {
  if (props.keyboardShortcut) {
    createShortcut(props.keyboardShortcut, props.action, {
      preventDefault: true,
    });
  }

  return (
    <a
      class="navbar-item"
      title={
        props.keyboardShortcut ? props.keyboardShortcut.join("+") : undefined
      }
      onClick={(ev) => {
        ev.preventDefault();
        props.action();
      }}
    >
      <span class="icon">
        <i class={props.icon}></i>
      </span>
      <span>{props.name}</span>
    </a>
  );
};

function makeStatusRequestHelper(url: string) {
  return async function (
    status: "open" | "close" | "ready" | "gay" | "blue-light",
  ) {
    let endpoint = new URL(url, window.location.href);

    return await api
      .post(endpoint, {
        searchParams: { status: status },
      })
      .json();
  };
}

async function makeSimpleRequest(url: string) {
  return await api.get(url).json();
}

async function amountRequest(url: string, message: string) {
  const input = prompt(message);
  if (!input) return;

  let amount: Big;
  try {
    amount = new Big(input);
  } catch (err) {
    alert("Invalid input.");
    return;
  }

  let formData = new FormData();
  formData.set("amount", amount.toString());

  const data: FallibleRequest<void> = await api
    .post(url, {
      body: formData,
    })
    .json();

  if (data["success"]) {
    alert("Success!");
  } else {
    alert(`Error: ${data.reason}`);
  }
}

const Actions: Component<{
  config: ApisConfig;
  setReadyForNext: Setter<boolean>;
  cartManager: CartManager;
}> = (props) => {
  const statusRequestHelper = makeStatusRequestHelper(
    props.config.urls.set_terminal_status,
  );

  return (
    <div class="navbar-dropdown is-right">
      <ActionButton
        name="Open Position"
        icon="fas fa-check"
        keyboardShortcut={["Alt", "O"]}
        action={() => statusRequestHelper("open")}
      />

      <ActionButton
        name="Close Position"
        icon="fas fa-window-close"
        keyboardShortcut={["Alt", "L"]}
        action={() => statusRequestHelper("close")}
      />

      <ActionButton
        name="Next Customer"
        icon="fas fa-forward"
        keyboardShortcut={["Alt", "N"]}
        action={() => {
          statusRequestHelper("ready");
          props.setReadyForNext(true);
        }}
      />

      <ActionButton
        name="Cancel Registration"
        icon="fas fa-user-slash"
        action={() => {
          props.cartManager.cancelRegistration();
        }}
      />

      <ActionButton
        name="Party Mode"
        icon="fas fa-rainbow"
        keyboardShortcut={["Alt", "G"]}
        action={() => statusRequestHelper("gay")}
      />

      <ActionButton
        name="Blue Light Special"
        icon="fas fa-k"
        keyboardShortcut={["Alt", "K"]}
        action={() => statusRequestHelper("blue-light")}
      />

      <Show
        when={
          props.config.permissions.cash_admin &&
          props.config.terminals.selected?.features?.cashdrawer
        }
      >
        <>
          <hr class="navbar-divider" />

          <ActionButton
            name="Open Drawer"
            icon="fas fa-money-bill-wave"
            action={() =>
              amountRequest(
                props.config.urls.open_drawer,
                "Enter initial amount in drawer",
              )
            }
          />

          <ActionButton
            name="Cash Deposit"
            icon="fas fa-plus"
            action={() =>
              amountRequest(
                props.config.urls.cash_deposit,
                "Enter amount added to drawer",
              )
            }
          />

          <ActionButton
            name="Safe Drop"
            icon="fas fa-vault"
            action={() =>
              amountRequest(
                props.config.urls.safe_drop,
                "Enter amount dropped into safe",
              )
            }
          />

          <ActionButton
            name="Cash Pickup"
            icon="fas fa-minus"
            action={() =>
              amountRequest(
                props.config.urls.cash_pickup,
                "Enter amount picked up from drawer",
              )
            }
          />

          <ActionButton
            name="Close Drawer"
            icon="fas fa-store-alt-slash"
            action={() =>
              amountRequest(
                props.config.urls.close_drawer,
                "Enter final amount in drawer",
              )
            }
          />

          <ActionButton
            name="No Sale"
            icon="fas fa-blender-phone fa-spin"
            action={() => makeSimpleRequest(props.config.urls.no_sale)}
          />
        </>
      </Show>
    </div>
  );
};

const KeyboardShortcuts: Component = () => {
  return (
    <Dialog preventScroll={false}>
      <Dialog.Trigger class="navbar-item" as="a">
        <span class="icon">
          <i class="fas fa-keyboard"></i>
        </span>
        <span>Keyboard Shortcuts</span>
      </Dialog.Trigger>
      <Dialog.Portal>
        <div class="modal is-active">
          <div class="modal-background"></div>

          <Dialog.Content class="modal-card">
            <header class="modal-card-head">
              <Dialog.Title as="h1" class="modal-card-title">
                Keyboard Shortcuts
              </Dialog.Title>
              <Dialog.CloseButton class="delete"></Dialog.CloseButton>
            </header>

            <section class="modal-card-body">
              <table class="table is-fullwidth">
                <tbody>
                  <For each={KNOWN_SHORTCUTS}>
                    {(entry) => (
                      <tr>
                        <th>
                          <code>{entry.shortcut}</code>
                        </th>
                        <td>{entry.description}</td>
                      </tr>
                    )}
                  </For>
                </tbody>
              </table>
            </section>
          </Dialog.Content>
        </div>
      </Dialog.Portal>
    </Dialog>
  );
};

const ToggleSetting: Component<{
  name: string;
  key: UserSettingKey;
  userSettings: UserSettingsManager;
}> = (props) => {
  return (
    <a
      href="#"
      class="navbar-item"
      onClick={(ev) => {
        ev.preventDefault();
        props.userSettings.store(
          props.key,
          !props.userSettings.userSettings()[props.key],
        );
      }}
    >
      <span class="icon">
        <Show
          when={props.userSettings.userSettings()[props.key]}
          fallback={<i class="fas fa-xmark"></i>}
        >
          <i class="fas fa-check"></i>
        </Show>
      </span>
      <span>{props.name}</span>
    </a>
  );
};

export const Navbar: Component<{
  setReadyForNext: Setter<boolean>;
  cartManager: CartManager;
}> = (props) => {
  const config = useContext(ConfigContext)!;
  const userSettings = useContext(UserSettingsContext)!;

  function switchTerminal(value: string) {
    console.debug(`Switching to terminal ${value}`);
    let url = new URL(window.location.href);
    url.searchParams.set("terminal", value);
    window.location.href = url.toString();
  }

  createEffect(() => {
    const availableIds = config.terminals.available.map(
      (terminal) => terminal.id,
    );
    if (
      availableIds.length > 0 &&
      config.terminals.selected &&
      !availableIds.includes(config.terminals.selected?.id)
    ) {
      switchTerminal(availableIds[0].toString());
    }
  });

  const [active, setActive] = createSignal<boolean>(false);

  return (
    <nav class="navbar" role="navigation">
      <div class="navbar-brand">
        <a class="navbar-item" href={config.urls.onsite_admin}>
          APIS Onsite Admin
        </a>

        <a
          role="button"
          class="navbar-burger"
          classList={{ "is-active": active() }}
          onClick={() => setActive(!active())}
        >
          <span></span>
          <span></span>
          <span></span>
          <span></span>
        </a>
      </div>

      <div class="navbar-menu" classList={{ "is-active": active() }}>
        <div class="navbar-end">
          <div class="navbar-item">
            <form>
              <div class="select">
                <select
                  name="terminal"
                  onChange={(ev) => switchTerminal(ev.target.value)}
                >
                  <For each={config.terminals.available}>
                    {(terminal) => (
                      <option
                        value={terminal.id}
                        selected={terminal.id === config.terminals.selected?.id}
                      >
                        {terminal.name}
                      </option>
                    )}
                  </For>
                </select>
              </div>
            </form>
          </div>

          <div class="navbar-item has-dropdown is-hoverable">
            <a class="navbar-link">
              <i class="fas fa-cog"></i>
            </a>

            <Actions
              config={config}
              setReadyForNext={props.setReadyForNext}
              cartManager={props.cartManager}
            />
          </div>

          <div class="navbar-item has-dropdown is-hoverable">
            <a class="navbar-link">
              <i class="fas fa-user"></i>
            </a>

            <div class="navbar-dropdown is-right">
              <ToggleSetting
                name="Full Width Layout"
                key="container_fluid"
                userSettings={userSettings}
              />

              <ToggleSetting
                name="Clear Cart After Print"
                key="clear_cart_after_print"
                userSettings={userSettings}
              />

              <ToggleSetting
                name="Search With Birthday"
                key="search_birthday"
                userSettings={userSettings}
              />

              <Show when={!!config.mqtt.auth.print_topic}>
                <ToggleSetting
                  name="Auto Print After Payment"
                  key="print_after_payment"
                  userSettings={userSettings}
                />
              </Show>

              <hr class="navbar-divider" />

              <KeyboardShortcuts />

              <hr class="navbar-divider" />

              <form method="post" action={config.urls.logout}>
                <input
                  type="hidden"
                  name="csrfmiddlewaretoken"
                  value={CSRF_TOKEN}
                />

                <button class="navbar-item has-text-danger">
                  <span class="icon">
                    <i class="fas fa-sign-out-alt"></i>
                  </span>
                  <span>Sign Out</span>
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};
