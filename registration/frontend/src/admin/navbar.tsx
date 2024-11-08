import { Big } from "big.js";
import { Component, createSignal, For, Show, useContext } from "solid-js";
import { createShortcut, KbdKey } from "@solid-primitives/keyboard";
import { render } from "solid-js/web";

import { ApisConfig, CSRF_TOKEN } from "../entrypoints/admin";
import { ConfigContext } from "./providers/config-provider";

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

async function makeSimpleRequest(url: string) {
  const resp = await fetch(url, {
    headers: {
      "x-csrftoken": CSRF_TOKEN,
    },
  });
  const data = await resp.json();

  return data;
}

async function amountRequest(url: string, message: string) {
  const input = prompt(message);
  let amount: Big;
  try {
    amount = new Big(input);
  } catch (err) {
    alert("Invalid input.");
    return;
  }

  let formData = new FormData();
  formData.set("amount", amount.toString());

  const resp = await fetch(url, {
    method: "POST",
    body: formData,
    headers: {
      "x-csrftoken": CSRF_TOKEN,
    },
  });
  const data = await resp.json();

  if (data["success"]) {
    alert("Success!");
  } else {
    alert(`Error: ${data.message}`);
  }
}

const Actions: Component<{ config: ApisConfig }> = (props) => {
  return (
    <div class="navbar-dropdown is-right">
      <ActionButton
        name="Open Position"
        icon="fas fa-check"
        keyboardShortcut={["Alt", "O"]}
        action={() => makeSimpleRequest(props.config.urls.open_terminal)}
      />

      <ActionButton
        name="Close Position"
        icon="fas fa-window-close"
        keyboardShortcut={["Alt", "L"]}
        action={() => makeSimpleRequest(props.config.urls.close_terminal)}
      />

      <ActionButton
        name="Next Customer"
        icon="fas fa-forward"
        keyboardShortcut={["Alt", "N"]}
        action={() => makeSimpleRequest(props.config.urls.ready_terminal)}
      />

      <Show when={props.config.permissions.cash_admin}>
        <>
          <hr class="navbar-divider" />

          <ActionButton
            name="Open Drawer"
            icon="fas fa-money-bill-wave"
            action={() =>
              amountRequest(
                props.config.urls.open_drawer,
                "Enter initial amount in drawer"
              )
            }
          />

          <ActionButton
            name="Cash Deposit"
            icon="fas fa-plus"
            action={() =>
              amountRequest(
                props.config.urls.cash_deposit,
                "Enter amount added to drawer"
              )
            }
          />

          <ActionButton
            name="Safe Drop"
            icon="fas fa-vault"
            action={() =>
              amountRequest(
                props.config.urls.safe_drop,
                "Enter amount dropped into safe"
              )
            }
          />

          <ActionButton
            name="Cash Pickup"
            icon="fas fa-minus"
            action={() =>
              amountRequest(
                props.config.urls.cash_pickup,
                "Enter amount picked up from drawer"
              )
            }
          />

          <ActionButton
            name="Close Drawer"
            icon="fas fa-store-alt-slash"
            action={() =>
              amountRequest(
                props.config.urls.close_drawer,
                "Enter final amount in drawer"
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

const Navbar: Component = () => {
  const config = useContext(ConfigContext);

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
                <select name="terminal">
                  <For each={config.terminals.available}>
                    {(terminal, index) => (
                      <option
                        selected={terminal.id === config.terminals.selected}
                        data-index={index()}
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

            <Actions config={config} />
          </div>

          <div class="navbar-item has-dropdown is-hoverable">
            <a class="navbar-link">
              <i class="fas fa-user"></i>
            </a>

            <div class="navbar-dropdown is-right">
              <a class="navbar-item has-text-danger" href={config.urls.logout}>
                <span class="icon">
                  <i class="fas fa-sign-out-alt"></i>
                </span>
                <span>Sign Out</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default function createActions(config: ApisConfig) {
  render(() => {
    return (
      <ConfigContext.Provider value={config}>
        <Navbar />
      </ConfigContext.Provider>
    );
  }, document.getElementById("admin-navbar"));
}
