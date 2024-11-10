import { Component, JSX, Show } from "solid-js";

export const MismatchedData: Component<{
  matched: boolean;
  message: string;
  children: JSX.Element;
}> = (props) => {
  return (
    <Show when={!props.matched} fallback={props.children}>
      <span class="icon-text has-text-danger" title={props.message}>
        <span class="icon">
          <i class="fa-solid fa-triangle-exclamation"></i>
        </span>
        {props.children}
      </span>
    </Show>
  );
};
