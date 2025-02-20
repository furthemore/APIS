import { Component, createEffect, Show } from "solid-js";

export const CartActionsError: Component<{ err: any; reset(): void }> = (
  props
) => {
  createEffect(() => {
    console.error("Cart had error", props.err);
  });

  return (
    <div class="message is-danger">
      <div class="message-header">
        <p>Cart Error</p>

        <button class="delete" onClick={() => props.reset()}></button>
      </div>

      <Show
        when={props.err.toString().length > 0}
        fallback={<div class="message-body">An unknown error occured.</div>}
      >
        <div class="message-body">{props.err.toString()}</div>
      </Show>
    </div>
  );
};
