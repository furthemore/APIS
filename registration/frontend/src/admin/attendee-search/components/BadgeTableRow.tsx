import { Component, createEffect, createSignal, Show } from "solid-js";

import { BadgeResult } from "..";
import { CartManager } from "../../cart";

export const BadgeTableRow: Component<{
  cartManager: CartManager;
  badge: BadgeResult;
  selected: boolean;
  searchQuery?: string;
}> = (props) => {
  const [loading, setLoading] = createSignal<boolean>(false);

  let row!: HTMLTableRowElement;

  createEffect(() => {
    if (props.selected) {
      row?.scrollIntoView({
        behavior: "auto",
        block: "nearest",
        inline: "nearest",
      });
    }
  });

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

  const hasSearchedId = () =>
    !!props.searchQuery &&
    parseInt(props.searchQuery, 10) === props.badge.badgeNumber;

  const hasIdenticalBadgeName = () =>
    props.searchQuery?.localeCompare(props.badge.badgeName, undefined, {
      sensitivity: "base",
    }) === 0;

  const hasIdenticalBadge = () => hasSearchedId() || hasIdenticalBadgeName();

  const alreadyInCart = () => props.cartManager.alreadyInCart(props.badge.id);

  return (
    <tr ref={row} classList={{ "is-link": props.selected }}>
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
        class="is-vcentered badge-name"
        classList={{ "is-success": hasIdenticalBadge() }}
        title={hasIdenticalBadge() ? "Badge is identical to search" : undefined}
      >
        <span>{props.badge.badgeName}</span>
        <Show when={props.badge.badgeNumber}>
          <span class="tag is-info ml-1">{props.badge.badgeNumber}</span>
        </Show>
      </td>
      <td class="is-vcentered">{props.badge.abandoned}</td>
      <td class="is-vcentered">
        <div class="buttons is-right badge-actions">
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
            classList={{ "is-loading": loading() }}
            disabled={alreadyInCart()}
            onClick={async (ev) => {
              ev.preventDefault();
              setLoading(true);
              await props.cartManager.addCartId(props.badge.id);
              setLoading(false);
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
