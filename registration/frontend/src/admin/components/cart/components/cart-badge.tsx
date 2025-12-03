import { faPaw, faPrint, faTrash } from "@fortawesome/free-solid-svg-icons";
import Fa from "solid-fa";
import { type Component, Show } from "solid-js";

import {
  type Badge,
  urlForBadge,
  useClearBadgePrinted,
  useRemoveBadgeFromCart,
} from "@admin/api";
import { Button } from "@components/button";

import { cleanMoneyAmount } from "../utils";

export const CartBadge: Component<{
  badge: Badge;
  hoveredOrderIdSelector: (key?: number) => boolean;
}> = (props) => {
  const clearBadgePrinted = useClearBadgePrinted();

  const removeBadgeFromCart = useRemoveBadgeFromCart();
  const isRemovingBadge = () => removeBadgeFromCart.isPending;

  return (
    <div
      class="card flush-table h-100"
      classList={{
        "border-warning": props.hoveredOrderIdSelector(props.badge.orderId),
      }}
    >
      <div class="card-header d-flex column-gap-2 align-items-center">
        <div class="flex-grow-1">
          <Fa icon={faPaw} fw class="me-1" />

          <a href={urlForBadge(props.badge.id).toString()} target="edit">
            {`${props.badge.firstName} ${props.badge.lastName}`}
          </a>

          <div class="d-flex align-items-center column-gap-2 flex-wrap">
            <span
              class="badge"
              classList={{
                "text-bg-success": props.badge.abandoned === "Paid",
                "text-bg-info": props.badge.abandoned === "Comp",
                "text-bg-warning": !["Paid", "Comp"].includes(
                  props.badge.abandoned,
                ),
              }}
            >
              {props.badge.abandoned}
            </span>

            <Show when={props.badge.holdType}>
              <span class="badge text-bg-danger">{props.badge.holdType}</span>
            </Show>

            <Show when={props.badge.printed}>
              <button
                class="btn badge text-bg-info"
                title="Already printed"
                onClick={() => {
                  if (confirm("Are you sure you need to reprint this badge?")) {
                    clearBadgePrinted.mutate(props.badge.id);
                  }
                }}
              >
                <Fa icon={faPrint} fw />
              </button>
            </Show>

            <Show when={props.badge.age < 18} fallback={"18+"}>
              <span class="text-danger text-uppercase">
                Minor Form Required
              </span>
            </Show>
          </div>
        </div>

        <Button
          type="button"
          class="btn btn-outline-danger"
          loading={isRemovingBadge()}
          onClick={() => removeBadgeFromCart.mutate(props.badge.id)}
        >
          <Fa icon={faTrash} fw />
        </Button>
      </div>

      <div class="card-body py-0">
        <table class="table-sm table">
          <thead>
            <tr>
              <th style={{ width: "60%" }}>Badge</th>
              <th style={{ width: "20%" }}>Level</th>
              <th style={{ width: "20%" }}>Price</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="badge-name">
                <span>{props.badge.badgeName}</span>
                <Show when={props.badge.badgeNumber}>
                  <span class="badge text-bg-info ms-1">
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
                    <span class="has-text-weight-semibold">
                      {props.badge.staff?.shirtSize || "None"}
                    </span>
                  </span>
                </td>
              </tr>
            </Show>
          </tbody>
        </table>
      </div>
    </div>
  );
};
