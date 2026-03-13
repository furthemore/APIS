import {
  faKeyboard,
  faSignOutAlt,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
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

import { CSRF_TOKEN } from "@admin/index";
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
  const [show, setShow] = createSignal(false);

  const selectedTerminalName = () =>
    config()?.terminals.available.find(
      (terminal) => terminal.id === config()?.terminals.selected?.id,
    )?.name || "No Terminal Selected";

  return (
    <nav class="navbar navbar-expand-sm bg-body-tertiary">
      <Container>
        <Link to="/registration/onsite/admin" class="navbar-brand">
          APIS Onsite Admin
        </Link>

        <button
          class="navbar-toggler"
          type="button"
          onClick={() => setShow((val) => !val)}
        >
          <span class="navbar-toggler-icon" />
        </button>

        <div
          class="navbar-collapse collapse flex-grow-0"
          classList={{ show: show() }}
        >
          <ul class="navbar-nav">
            <Show when={config()}>
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
                      <For each={config()?.terminals.available}>
                        {(terminal) => (
                          <DropdownMenu.Item as="li">
                            <Link
                              to="/registration/onsite/admin"
                              class="dropdown-item"
                              classList={{
                                active:
                                  terminal.id ===
                                  config()?.terminals.selected?.id,
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
                <Actions setReadyForNext={props.setReadyForNext} />
              </li>
            </Show>

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
                      name="Show Search Status"
                      key="showSearchStatus"
                    />

                    <ToggleSetting
                      name="Search With Birthday"
                      key="searchBirthday"
                    />

                    <Show when={config()?.mqtt?.auth?.print_topic}>
                      <ToggleSetting
                        name="Auto Print After Payment"
                        key="printAfterPayment"
                      />
                    </Show>

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

                    <DropdownMenu.Item>
                      <DropdownMenu.Separator class="dropdown-divider" />
                    </DropdownMenu.Item>

                    <DropdownMenu.Item as="li">
                      <form method="post" action="/accounts/logout/">
                        <input
                          type="hidden"
                          name="csrfmiddlewaretoken"
                          value={CSRF_TOKEN}
                        />

                        <button class="dropdown-item text-danger d-flex align-items-center column-gap-2">
                          <IconAndLabel
                            children="Sign Out"
                            icon={faSignOutAlt}
                            fw
                          />
                        </button>
                      </form>
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
