import { Component, JSX, Setter } from "solid-js";

export type ActionButtonKey = "cash" | "card" | "print";

export type ActionButtonProps = {
  button: ActionButtonKey;
  class: string;
  disabled: boolean;
  loadingButton?: ActionButtonKey;
  setLoadingButton: Setter<ActionButtonKey>;
  action: (ev: MouseEvent) => Promise<any>;
  children: JSX.Element;
};

export const ActionButton: Component<ActionButtonProps> = (props) => {
  let classes = `button is-fullwidth ${props.class}`;

  return (
    <div class="column">
      <button
        class={classes}
        classList={{ "is-loading": props.loadingButton == props.button }}
        disabled={props.loadingButton != null || props.disabled}
        onClick={(ev) => {
          trackLoadingButton(
            props.setLoadingButton,
            props.button,
            props.action(ev)
          );
        }}
      >
        {props.children}
      </button>
    </div>
  );
};

async function trackLoadingButton<T>(
  setLoadingButton: Setter<ActionButtonKey>,
  button: ActionButtonKey,
  action: Promise<T>
): Promise<T> {
  setLoadingButton(button);
  const resp = await action;
  setLoadingButton(null);
  return resp;
}
