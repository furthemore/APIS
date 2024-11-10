import { Component, createEffect, Show } from "solid-js";

import { BadgeResult } from "..";
import { CartManager } from "../../cart";

export const BadgeTableRow: Component<{
  cartManager: CartManager;
  badge: BadgeResult;
  searchQuery?: string;
}> = (props) => {
  const hasPreferredName = () =>
    props.badge.attendee.preferredName &&
    props.badge.attendee.preferredName.localeCompare(
      props.badge.attendee.firstName,
      undefined,
      { sensitivity: "base" }
    ) !== 0;

  const fullName = () =>
    `${props.badge.attendee.firstName} ${props.badge.attendee.lastName}`;

  const hasIdenticalName = () =>
    props.searchQuery?.localeCompare(fullName(), undefined, {
      sensitivity: "base",
    }) === 0;

  const hasIdenticalBadge = () =>
    props.searchQuery?.localeCompare(props.badge.badgeName, undefined, {
      sensitivity: "base",
    }) === 0;

  const alreadyInCart = () => props.cartManager.alreadyInCart(props.badge.id);

  return (
    <tr>
      <td
        class="is-vcentered"
        classList={{ "is-success": hasIdenticalName() }}
        title={hasIdenticalName() ? "Name is identical to search" : undefined}
      >
        <div>{fullName()}</div>

        <Show when={hasPreferredName()}>
          <div>
            <span class="is-italic mr-1">Preferred:</span>
            <span class="has-text-weight-semibold">
              {props.badge.attendee.preferredName}
            </span>
          </div>
        </Show>
      </td>
      <td
        class="is-vcentered"
        classList={{ "is-success": hasIdenticalBadge() }}
        title={hasIdenticalBadge() ? "Badge is identical to search" : undefined}
      >
        {props.badge.badgeName}
      </td>
      <td class="is-vcentered">{props.badge.abandoned}</td>
      <td class="is-vcentered">
        <div class="buttons is-right">
          <a
            href={props.badge.edit_url}
            target="edit"
            class="button is-small is-info"
          >
            <span class="icon">
              <i class="fas fa-edit"></i>
            </span>
          </a>

          <button
            class="button is-small is-primary"
            disabled={alreadyInCart()}
            onClick={(ev) => {
              ev.preventDefault();
              props.cartManager.addCartId(props.badge.id);
            }}
          >
            <span class="icon">
              <i class="fas fa-cart-shopping"></i>
            </span>
          </button>
        </div>
      </td>
    </tr>
  );
};
