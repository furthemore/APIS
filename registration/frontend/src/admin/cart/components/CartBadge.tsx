import { Component, createResource, createSignal, Show } from "solid-js";

import { Badge, CartManager } from "../cart-manager";
import { cleanMoneyAmount } from "./CartEntries";

export const CartBadge: Component<{ manager: CartManager; badge: Badge }> = (
  props
) => {
  const [clearPrintBadgeId, setClearPrintBadgeId] = createSignal<number>();
  const [clearPrint] = createResource(clearPrintBadgeId, async (id) => {
    const resp = await props.manager.clearBadgePrinted(id);
    if (resp.success) {
      await props.manager.refreshCart();
    } else {
      alert("Unable to clear badge print flag.");
    }
  });

  const [removeBadgeId, setRemoveBadgeId] = createSignal<number>();
  const [remove] = createResource(removeBadgeId, async (id) => {
    await props.manager.removeBadge(id);
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
                class="tag is-link"
                classList={{ "is-loading": clearPrint.loading }}
                title="Already printed"
                onClick={() => {
                  if (
                    confirm(
                      "Are you sure you need to clear the print flag for this badge?"
                    )
                  ) {
                    setClearPrintBadgeId(props.badge.id);
                  }
                }}
              >
                <span class="icon">
                  <i class="fas fa-print" />
                </span>
              </button>
            </Show>
          </div>

          <div class="mr-2 is-flex-grow-1">
            <a href={props.manager.urlForBadge(props.badge.id)} target="edit">
              {`${props.badge.firstName} ${props.badge.lastName}`}
            </a>
          </div>

          <div>
            <Show when={props.badge.age < 18} fallback={"18+"}>
              <span class="has-text-danger is-uppercase">
                Minor Form Required
              </span>
            </Show>
          </div>

          <div>
            <button
              class="delete"
              classList={{ "is-loading": remove.loading }}
              onClick={(ev) => {
                ev.preventDefault();
                setRemoveBadgeId(props.badge.id);
              }}
            ></button>
          </div>
        </div>

        <div class="message-body p-0">
          <table class="table is-fullwidth is-narrow">
            <thead>
              <tr>
                <th style="width: 60%;">Badge</th>
                <th style="width: 20%;">Level</th>
                <th style="width: 20%;">Price</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="badge-name">
                  <span>{props.badge.badgeName}</span>
                  <Show when={props.badge.badgeNumber}>
                    <span class="tag is-info ml-1">
                      {props.badge.badgeNumber}
                    </span>
                  </Show>
                </td>
                <td>{props.badge.effectiveLevel?.name || ""}</td>
                <td>{cleanMoneyAmount(props.badge.effectiveLevel?.price)}</td>
              </tr>
              <Show when={props.badge.staff}>
                <tr>
                  <td colSpan={3}>
                    <span>
                      {`Staff Shirt – `}
                      <span class="has-text-weight-semibold">{props.badge.staff?.shirtSize || "None"}</span>
                    </span>
                  </td>
                </tr>
              </Show>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
