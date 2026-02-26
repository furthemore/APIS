import { faPaw, faPrint, faTrash } from "@fortawesome/free-solid-svg-icons";
import { ContextMenu } from "@kobalte/core/context-menu";
import { useQueryClient } from "@tanstack/solid-query";
import Fa from "solid-fa";
import { type Component, Show, createMemo, useContext } from "solid-js";

import {
  type AttendeeDetails,
  type BadgeCart,
  type BadgeState,
  attendeeDetailsOptions,
  urlForBadge,
  urlForOnsiteDetails,
  useClearBadgePrinted,
  useGetToken,
  useRemoveBadgeFromCart,
} from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";
import { MqttContext } from "@admin/providers/mqtt-provider";
import { Button } from "@components/button";

import { cleanMoneyAmount } from "../utils";

const STATE_COLORS: Record<BadgeState, string> = {
  Abandoned: "text-bg-warning",
  Unpaid: "text-bg-warning",
  Comp: "text-bg-success",
  Paid: "text-bg-success",
  Dealer: "text-bg-info",
  Staff: "text-bg-primary",
};

const BADGE_SYMBOLS: [RegExp, string][] = [
  [/fox/gi, "🦊"],
  [/wolf/gi, "🐺"],
  [/cat|kitty/gi, "🐈"],
  [/frog/gi, "🐸"],
];

type AttendeeDetailField = keyof AttendeeDetails;

const BASIC_FIELDS: AttendeeDetailField[] = [
  "address1",
  "address2",
  "city",
  "state",
  "country",
  "postalCode",
];
const CLONE_FIELDS: AttendeeDetailField[] = (
  ["lastName", "email", "phone"] as AttendeeDetailField[]
).concat(BASIC_FIELDS);

const filterDetails = (
  details: AttendeeDetails,
  fields: AttendeeDetailField[],
): AttendeeDetails => {
  for (const detailKey in details) {
    const key = detailKey as AttendeeDetailField;
    if (!fields.includes(key)) delete details[key];
  }
  return details;
};

type FieldType = "basic" | "clone";

export const CartBadge: Component<{
  badge: BadgeCart;
  hoveredOrderIdSelector: (key?: number) => boolean;
}> = (props) => {
  const config = useContext(ConfigContext)!;
  const mqtt = useContext(MqttContext)!;
  const queryClient = useQueryClient();

  const clearBadgePrinted = useClearBadgePrinted();

  const removeBadgeFromCart = useRemoveBadgeFromCart();
  const isRemovingBadge = () => removeBadgeFromCart.isPending;

  const regToken = useGetToken();

  const badgeSymbol = createMemo(() => {
    const badgeName = props.badge.badgeName;

    return BADGE_SYMBOLS.find(([matcher]) => {
      return matcher.test(badgeName);
    })?.[1];
  });

  const createFromBadge = async (type: FieldType, prompt: boolean) => {
    const attendeeDetails = await queryClient.ensureQueryData(
      attendeeDetailsOptions(props.badge.id),
    );

    const details = filterDetails(
      { ...(attendeeDetails.attendee || {}) },
      type === "basic" ? BASIC_FIELDS : CLONE_FIELDS,
    );

    if (prompt) {
      const resp = await regToken.mutateAsync();
      await mqtt()?.displayRegistration(resp.token, details);
    } else {
      const url = urlForOnsiteDetails(details);
      window.open(url, "register");
    }
  };

  return (
    <ContextMenu preventScroll={false}>
      <ContextMenu.Trigger
        class="card flush-table h-100"
        classList={{
          "border-warning": props.hoveredOrderIdSelector(props.badge.orderId),
        }}
      >
        <div class="card-header d-flex column-gap-2 align-items-center">
          <div class="flex-grow-1">
            <Show
              when={badgeSymbol()}
              fallback={<Fa icon={faPaw} fw class="me-1" />}
            >
              <span class="me-1" style={{ height: "1.25em", width: "1.25em" }}>
                {badgeSymbol()}
              </span>
            </Show>

            <a href={urlForBadge(props.badge.id).toString()} target="edit">
              {`${props.badge.firstName} ${props.badge.lastName}`}
            </a>

            <div class="d-flex align-items-center column-gap-2 flex-wrap">
              <span class={`badge ${STATE_COLORS[props.badge.abandoned]}`}>
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
                    if (
                      confirm("Are you sure you need to reprint this badge?")
                    ) {
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
                <th class="text-end" style={{ width: "20%" }}>
                  Price
                </th>
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
                <td class="text-end">
                  {cleanMoneyAmount(props.badge.effectiveLevel?.price)}
                </td>
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
      </ContextMenu.Trigger>

      <ContextMenu.Portal>
        <ContextMenu.Content class="dropdown is-active">
          <div class="dropdown-menu show">
            <ContextMenu.Item
              as="button"
              class="dropdown-item"
              onClick={() => createFromBadge("basic", false)}
            >
              New Adult
            </ContextMenu.Item>

            <ContextMenu.Item
              as="button"
              class="dropdown-item"
              onClick={() => createFromBadge("clone", false)}
            >
              New Child
            </ContextMenu.Item>

            <Show when={config()?.terminals?.selected?.features.prompt}>
              <ContextMenu.Item
                as="button"
                class="dropdown-item"
                onClick={() => createFromBadge("basic", true)}
              >
                Prompt Adult
              </ContextMenu.Item>

              <ContextMenu.Item
                as="button"
                class="dropdown-item"
                onClick={() => createFromBadge("clone", false)}
              >
                Prompt Child
              </ContextMenu.Item>
            </Show>
          </div>
        </ContextMenu.Content>
      </ContextMenu.Portal>
    </ContextMenu>
  );
};
