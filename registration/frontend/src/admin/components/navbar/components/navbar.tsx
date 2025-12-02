import {
  faBell,
  faKeyboard,
  faSignOutAlt,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
import { createPermission } from "@solid-primitives/permission";
import { Link } from "@tanstack/solid-router";
import Fa from "solid-fa";
import {
  type Component,
  For,
  type Setter,
  Show,
  createSignal,
  useContext,
} from "solid-js";

import { ConfigContext } from "@admin/providers/config-provider";
import { Container } from "@components/container";
import { IconAndLabel } from "@components/icon-and-label";

import { Actions } from "./actions";
import { KeyboardShortcuts } from "./keyboard-shortcuts";
import { ToggleSetting } from "./toggle-setting";

export const Navbar: Component<{
  setReadyForNext: Setter<boolean>;
}> = (props) => {
  const config = useContext(ConfigContext)!;

  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = createSignal(false);

  const selectedTerminalName = () =>
    config.terminals.available.find(
      (terminal) => terminal.id === config.terminals.selected?.id,
    )?.name;

  const notificationPermission = createPermission({ name: "notifications" });
  const canPromptForNotification = () => notificationPermission() === "prompt";

  return (
    <nav class="navbar navbar-expand-sm bg-body-tertiary">
      <Container>
        <Link to="/registration/onsite/admin" class="navbar-brand">
          APIS Onsite Admin
        </Link>

        <div class="navbar-collapse collapse flex-grow-0">
          <ul class="navbar-nav">
            <li class="nav-item dropdown">
              <DropdownMenu>
                <DropdownMenu.Trigger
                  as="button"
                  class="nav-link dropdown-toggle"
                >
                  {selectedTerminalName()}
                </DropdownMenu.Trigger>

                <DropdownMenu.Portal>
                  <DropdownMenu.Content as="ul" class="dropdown-menu show">
                    <For each={config.terminals.available}>
                      {(terminal) => (
                        <DropdownMenu.Item as="li">
                          <Link
                            to="/registration/onsite/admin"
                            class="dropdown-item"
                            classList={{
                              active:
                                terminal.id === config.terminals.selected?.id,
                            }}
                            search={{ terminal: terminal.id }}
                          >
                            {terminal.name}
                          </Link>
                        </DropdownMenu.Item>
                      )}
                    </For>
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu>
            </li>

            <li class="nav-item dropdown">
              <Actions
                config={config}
                setReadyForNext={props.setReadyForNext}
              />
            </li>

            <li class="nav-item dropdown">
              <KeyboardShortcuts
                signal={[showKeyboardShortcuts, setShowKeyboardShortcuts]}
              />

              <DropdownMenu>
                <DropdownMenu.Trigger
                  as="button"
                  class="nav-link dropdown-toggle"
                >
                  <Fa icon={faUser} />
                </DropdownMenu.Trigger>

                <DropdownMenu.Portal>
                  <DropdownMenu.Content as="ul" class="dropdown-menu show">
                    <ToggleSetting
                      name="Full Width Layout"
                      key="containerFluid"
                    />

                    <ToggleSetting
                      name="Multiple Badge Columns"
                      key="multipleBadgeColumns"
                    />

                    <ToggleSetting
                      name="Search With Birthday"
                      key="searchBirthday"
                    />

                    <Show
                      when={config.terminals.selected?.features?.printViaMqtt}
                    >
                      <ToggleSetting
                        name="Auto Print After Payment"
                        key="printAfterPayment"
                      />
                    </Show>

                    <ToggleSetting
                      name="Clear Cart After Print"
                      key="clearCartAfterPrint"
                    />

                    <DropdownMenu.Item>
                      <DropdownMenu.Separator class="dropdown-divider" />
                    </DropdownMenu.Item>

                    <DropdownMenu.Item as="li">
                      <button
                        class="dropdown-item"
                        onClick={() => setShowKeyboardShortcuts(true)}
                      >
                        <IconAndLabel
                          children="Keyboard Shortcuts"
                          icon={faKeyboard}
                          fw
                        />
                      </button>
                    </DropdownMenu.Item>

                    <Show when={canPromptForNotification()}>
                      <DropdownMenu.Item as="li">
                        <button
                          class="dropdown-item"
                          onClick={() => Notification.requestPermission()}
                        >
                          <IconAndLabel
                            children="Allow Notifications"
                            icon={faBell}
                            fw
                          />
                        </button>
                      </DropdownMenu.Item>
                    </Show>

                    <DropdownMenu.Item>
                      <DropdownMenu.Separator class="dropdown-divider" />
                    </DropdownMenu.Item>

                    <DropdownMenu.Item as="li">
                      <a
                        href="/registration/logout"
                        class="dropdown-item text-danger d-flex align-items-center column-gap-2"
                      >
                        <IconAndLabel
                          children="Sign Out"
                          icon={faSignOutAlt}
                          fw
                        />
                      </a>
                    </DropdownMenu.Item>
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu>
            </li>
          </ul>
        </div>
      </Container>
    </nav>
  );
};
