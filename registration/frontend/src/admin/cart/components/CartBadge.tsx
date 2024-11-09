import { Component, createResource, createSignal, Show } from "solid-js";

import { Badge, CartManager } from "../cart-manager";
import { cleanMoneyAmount } from "./CartEntries";

export const CartBadge: Component<{ manager: CartManager; badge: Badge }> = (
  props
) => {
  const [clearBadgeId, setClearBadgeId] = createSignal<number>();
  const [resource] = createResource(clearBadgeId, async (id) => {
    const resp = await props.manager.clearBadgePrinted(id);
    if (resp.success) {
      await props.manager.printBadges([id]);
    } else {
      alert("Unable to clear badge print flag.");
    }
  });

  return (
    <div class="block control">
      <div class="message">
        <div class="message-header is-justify-content-start">
          <div class="tags is-flex-wrap-nowrap mb-0 mr-2">
            <span
              class="tag"
              classList={{
                "is-success": props.badge.abandoned === "Paid",
                "is-info": props.badge.abandoned === "Comp",
                "is-warning": !["Paid", "Comp"].includes(props.badge.abandoned),
              }}
            >
              {props.badge.abandoned}
            </span>

            <Show when={props.badge.holdType}>
              <span class="tag is-danger">{props.badge.holdType}</span>
            </Show>

            <Show when={props.badge.printed}>
              <button
                class="tag is-danger"
                classList={{ "is-loading": resource.loading }}
                title="Already printed"
                onClick={() => {
                  if (
                    confirm("Are you sure you need to re-print this badge?")
                  ) {
                    setClearBadgeId(props.badge.id);
                  }
                }}
              >
                <span class="icon">
                  <i class="fas fa-print" />
                </span>
              </button>
            </Show>

            <Show when={props.badge.badgeNumber}>
              <span class="tag is-info">{props.badge.badgeNumber}</span>
            </Show>
          </div>

          <div class="mr-2 is-flex-grow-1">
            <a href={props.manager.urlForBadge(props.badge.id)} target="edit">
              {`${props.badge.firstName} ${props.badge.lastName}`}
            </a>
          </div>

          <div>
            <Show when={props.badge.age < 18} fallback={"18+"}>
              <span class="has-text-danger">MINOR FORM REQUIRED</span>
            </Show>
          </div>

          <div>
            <button
              class="delete"
              onClick={(ev) => {
                ev.preventDefault();
                props.manager.removeBadge(props.badge.id);
              }}
            ></button>
          </div>
        </div>

        <div class="message-body p-0">
          <table class="table is-fullwidth is-condensed">
            <thead>
              <tr>
                <th style="width: 50%;">Badge Name</th>
                <th style="width: 25%;">Level</th>
                <th style="width: 25%;">Price</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{props.badge.badgeName}</td>
                <td>{props.badge.effectiveLevel?.name || ""}</td>
                <td>{cleanMoneyAmount(props.badge.effectiveLevel?.price)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
