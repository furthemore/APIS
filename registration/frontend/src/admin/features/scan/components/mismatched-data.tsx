import { faTriangleExclamation } from "@fortawesome/free-solid-svg-icons";
import Fa from "solid-fa";
import { type Component, type JSX, Show } from "solid-js";

export const MismatchedData: Component<{
  matched: boolean;
  message: string;
  children: JSX.Element;
}> = (props) => {
  return (
    <Show when={!props.matched} fallback={props.children}>
      <span title={props.message} class="text-danger">
        <Fa icon={faTriangleExclamation} fw class="me-1" />
        {props.children}
      </span>
    </Show>
  );
};
