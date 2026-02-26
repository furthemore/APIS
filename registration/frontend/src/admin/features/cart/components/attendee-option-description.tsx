import { type Component, Match, Show, Switch, useContext } from "solid-js";

import type { AttendeeOption } from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";

import { cleanMoneyAmount, getShirtSizeName } from "../utils";

export const AttendeeOptionDescription: Component<{ item: AttendeeOption }> = (
  props,
) => {
  const config = useContext(ConfigContext)!;

  return (
    <td>
      <div title={props.item.reason}>
        {`${props.item.quantity} × ${props.item.item} (${cleanMoneyAmount(props.item.price)}/ea)`}
        <Show
          when={
            props.item.optionExtraType === "ShirtSizes" ||
            props.item.optionExtraType == "bool"
          }
        >
          {` - `}
          <span class="has-text-weight-bold">
            <Switch>
              <Match when={props.item.optionExtraType === "ShirtSizes"}>
                {getShirtSizeName(config(), props.item.optionValue)}
              </Match>
              <Match when={props.item.optionExtraType === "bool"}>
                {props.item.optionValue === "True" ? "Yes" : "No"}
              </Match>
            </Switch>
          </span>
        </Show>
      </div>
      <Show when={props.item.optionExtraType === "string"}>
        <div class="has-text-weight-bold">{props.item.optionValue}</div>
      </Show>
    </td>
  );
};
