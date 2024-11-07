import { Component, Show } from "solid-js";

import { Badge, CartManager } from "../cart-manager";

export const CartBadge: Component<{ manager: CartManager; badge: Badge }> = (
  props
) => {
  return (
    <div class="panel panel-default">
      <div class="panel-heading">
        <span
          classList={{
            label: true,
            "label-success": props.badge.abandoned === "Paid",
            "label-info": props.badge.abandoned === "Comp",
            "label-warning": !["Paid", "Comp"].includes(props.badge.abandoned),
          }}
        >
          {props.badge.abandoned}
        </span>

        <Show when={props.badge.holdType}>
          <span class="label label-danger">{props.badge.holdType}</span>
        </Show>

        <Show when={props.badge.printed}>
          <span class="label label-danger" title="Already printed">
            <i class="fas fa-print" />
          </span>
        </Show>

        <Show when={props.badge.badgeNumber}>
          <span class="label label-info">{props.badge.badgeNumber}</span>
        </Show>

        <a href={props.manager.urlForBadge(props.badge.id)} target="_blank">
          {`${props.badge.firstName} ${props.badge.lastName}`}
        </a>

        <a
          href="#"
          style={"color: darkred;"}
          onClick={(ev) => {
            ev.preventDefault();
            props.manager.removeBadge(props.badge.id);
          }}
        >
          <i class="fas fa-trash-can"></i>
        </a>

        <Show when={props.badge.age < 18} fallback={"18+"}>
          <span style={"color: red;"}>MINOR FORM REQUIRED</span>
        </Show>
      </div>

      <table class="table">
        <thead>
          <tr>
            <th>Badge Name</th>
            <th>Level</th>
            <th>Price</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{props.badge.badgeName}</td>
            <td>{props.badge.effectiveLevel?.name || ""}</td>
            <td>{props.badge.effectiveLevel?.price || "0.00"}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};
