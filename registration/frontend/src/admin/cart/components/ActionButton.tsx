import { createShortcut, KbdKey } from "@solid-primitives/keyboard";
import {
  Component,
  createEffect,
  createResource,
  createSignal,
  JSX,
  Setter,
} from "solid-js";

export type ActionButtonProps = {
  class: string;
  disabled: boolean;
  loading: boolean;
  setLoading: Setter<boolean>;
  keyboardShortcut?: KbdKey[];
  action: (ev: Event) => Promise<any> | undefined;
  children: JSX.Element;
};

export const ActionButton: Component<ActionButtonProps> = (props) => {
  const [triggerEvent, setTriggerEvent] = createSignal<Event>();
  const [resource] = createResource(triggerEvent, async (ev) => {
    props.setLoading(true);
    const resp = await props.action(ev);
    props.setLoading(false);
    return resp;
  });

  const loadingDisabled = () => props.disabled || props.loading;

  if (props.keyboardShortcut) {
    createShortcut(
      props.keyboardShortcut,
      (ev) => {
        if (loadingDisabled()) return;
        setTriggerEvent(ev || undefined);
      },
      {
        preventDefault: true,
      }
    );
  }

  createEffect(() => {
    // When we have an error, throw it up. All of the buttons are wrapped in an
    // error boundary so an appropriately sized message can display.
    const err = resource.error;
    if (err) {
      throw err;
    }
  });

  return (
    <div class="column">
      <button
        class={`button is-fullwidth ${props.class}`}
        classList={{ "is-loading": resource.loading }}
        disabled={loadingDisabled()}
        title={
          props.keyboardShortcut ? props.keyboardShortcut.join("+") : undefined
        }
        onClick={(ev) => {
          setTriggerEvent(ev);
        }}
      >
        {props.children}
      </button>
    </div>
  );
};
