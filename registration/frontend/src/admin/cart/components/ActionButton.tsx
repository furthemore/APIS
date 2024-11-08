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
  action: (ev: MouseEvent) => Promise<any>;
  children: JSX.Element;
};

export const ActionButton: Component<ActionButtonProps> = (props) => {
  const [triggerEvent, setTriggerEvent] = createSignal<MouseEvent>();
  const [resource] = createResource(triggerEvent, async (ev) => {
    console.debug("Attempting to perform button action");
    props.setLoading(true);
    const resp = await props.action(ev);
    props.setLoading(false);
    return resp;
  });

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
        disabled={props.loading || props.disabled}
        onClick={(ev) => {
          setTriggerEvent(ev);
        }}
      >
        {props.children}
      </button>
    </div>
  );
};
