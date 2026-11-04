import { faCartShopping } from "@fortawesome/free-solid-svg-icons";
import { ContextMenu } from "@kobalte/core/context-menu";
import Fa from "solid-fa";
import { type Component, Show, createEffect } from "solid-js";

import { type BadgeResult, useAddBadgeToCart } from "@admin/api";
import { Button } from "@components/button";

export const BadgeTableRow: Component<{
  badge: BadgeResult;
  inCart: boolean;
  selected: boolean;
  showStatus: boolean;
  searchQuery?: string;
}> = (props) => {
  const addBadgeToCart = useAddBadgeToCart();

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

  const cleanedSearchQuery = () => props.searchQuery?.trim();

  const hasPreferredName = () =>
    props.badge.attendee.preferredName &&
    props.badge.attendee.preferredName.localeCompare(
      props.badge.attendee.firstName,
      undefined,
      { sensitivity: "base" },
    ) !== 0;

  const fullName = () =>
    `${props.badge.attendee.firstName} ${props.badge.attendee.lastName}`;

  const hasIdenticalName = () =>
    cleanedSearchQuery()?.localeCompare(fullName(), undefined, {
      sensitivity: "base",
    }) === 0;

  const hasSearchedId = () => {
    const query = cleanedSearchQuery();
    return query && Number.parseInt(query, 10) === props.badge.badgeNumber;
  };

  const hasIdenticalBadgeName = () =>
    cleanedSearchQuery()?.localeCompare(props.badge.badgeName, undefined, {
      sensitivity: "base",
    }) === 0;

  const hasIdenticalBadge = () => hasSearchedId() || hasIdenticalBadgeName();

  return (
    <ContextMenu preventScroll={false}>
      <ContextMenu.Trigger
        as="tr"
        ref={row}
        classList={{ "table-active": props.selected }}
      >
        <td
          classList={{ "table-success": hasIdenticalName() }}
          title={hasIdenticalName() ? "Name is identical to search" : undefined}
        >
          <div>{fullName()}</div>

          <Show when={hasPreferredName()}>
            <div>
              <span class="fst-italic me-1">Preferred:</span>
              <span class="fw-semibold">
                {props.badge.attendee.preferredName}
              </span>
            </div>
          </Show>
        </td>
        <td
          class="badge-name"
          classList={{ "table-success": hasIdenticalBadge() }}
          title={
            hasIdenticalBadge() ? "Badge is identical to search" : undefined
          }
        >
          <span>{props.badge.badgeName}</span>
          <Show when={props.badge.badgeNumber}>
            <span class="badge text-bg-info ms-1">
              {props.badge.badgeNumber}
            </span>
          </Show>
        </td>
        <Show when={props.showStatus}>
          <td>{props.badge.abandoned}</td>
        </Show>
        <td class="text-end">
          <div class="btn-group">
            <Button
              type="button"
              class="btn btn-sm btn-primary"
              loading={addBadgeToCart.isPending}
              disabled={props.inCart}
              onClick={() => {
                addBadgeToCart.mutate(props.badge.id);
              }}
            >
              <Fa icon={faCartShopping} fw />
            </Button>
          </div>
        </td>
      </ContextMenu.Trigger>

      <ContextMenu.Portal>
        <ContextMenu.Content class="dropdown is-active">
          <div class="dropdown-menu show">
            <ContextMenu.Item
              as="a"
              href={props.badge.editUrl}
              target="edit"
              class="dropdown-item"
            >
              Open in Admin
            </ContextMenu.Item>
          </div>
        </ContextMenu.Content>
      </ContextMenu.Portal>
    </ContextMenu>
  );
};
