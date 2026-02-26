import { type KbdKey, createShortcut } from "@solid-primitives/keyboard";
import {
  type Component,
  type JSX,
  type Setter,
  createEffect,
  createResource,
  createSignal,
} from "solid-js";

import { Button } from "@components/button";

export type ActionButtonProps = {
  class: string;
  disabled: boolean;
  setLoading: Setter<boolean>;
  keyboardShortcut?: KbdKey[];
  action: (holdingShift: boolean) => Promise<unknown> | undefined;
  children: JSX.Element;
};

export const ActionButton: Component<ActionButtonProps> = (props) => {
  const [triggerEvent, setTriggerEvent] = createSignal<
    MouseEvent | KeyboardEvent
  >();

  // eslint-disable-next-line solid/reactivity
  const [result] = createResource(triggerEvent, (ev) => {
    return props.action(ev.shiftKey);
  });

  const title = () =>
    props.keyboardShortcut ? props.keyboardShortcut.join("+") : undefined;

  createEffect(() => {
    props.setLoading(result.loading);
  });

  createEffect(() => {
    if (props.keyboardShortcut) {
      createShortcut(
        props.keyboardShortcut,
        (ev) => {
          if (props.disabled) return;
          setTriggerEvent(ev || undefined);
        },
        {
          preventDefault: true,
        },
      );
    }
  });

  return (
    <div class="col">
      <Button
        type="button"
        class={`btn ${props.class} w-100 text-nowrap`}
        loading={result.loading}
        disabled={props.disabled}
        title={title()}
        onClick={setTriggerEvent}
      >
        {props.children}
      </Button>
    </div>
  );
};
