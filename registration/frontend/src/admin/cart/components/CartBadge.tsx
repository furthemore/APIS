import { ContextMenu } from "@kobalte/core/context-menu";
import {
  type Component,
  Show,
  createResource,
  createSignal,
  useContext,
} from "solid-js";

import { type AttendeeDetails } from "../../components/DisplayRegistration";
import { ConfigContext } from "../../providers/config-provider";
import { type Badge, CartManager } from "../cart-manager";
import { cleanMoneyAmount } from "./CartEntries";

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

const createAttendee = async (
  cartManager: CartManager,
  badgeId: number,
  onlyBasic: boolean,
  prompt: boolean,
) => {
  const details = await cartManager.fetchAttendeeDetails(badgeId);
  if (!details.success) {
    return alert("Unable to get attendee details");
  }

  const fields = filterDetails(
    details.attendee,
    onlyBasic ? BASIC_FIELDS : CLONE_FIELDS,
  );

  if (prompt) {
    await cartManager.displayRegistration(fields);
  } else {
    const url = cartManager.getOnsiteUrl(fields);
    window.open(url, "register");
  }
};

export const CartBadge: Component<{ manager: CartManager; badge: Badge }> = (
  props,
) => {
  const config = useContext(ConfigContext)!;

  const [clearPrintBadgeId, setClearPrintBadgeId] = createSignal<number>();
  createResource(clearPrintBadgeId, async (id) => {
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

  const promptClearPrint = () => {
    if (
      confirm("Are you sure you need to clear the print flag for this badge?")
    ) {
      setClearPrintBadgeId(props.badge.id);
    }
  };

  const create = (onlyBasic: boolean, prompt: boolean) =>
    createAttendee(props.manager, props.badge.id, onlyBasic, prompt);

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
              <span class="tag is-link" title="Already printed">
                <span class="icon">
                  <i class="fas fa-print" />
                </span>
              </span>
            </Show>
          </div>

          <div class="mr-2 is-flex-grow-1">
            <ContextMenu preventScroll={false}>
              <ContextMenu.Trigger
                as="a"
                href={props.manager.urlForBadge(props.badge.id)}
                target="edit"
              >
                {`${props.badge.firstName} ${props.badge.lastName}`}
              </ContextMenu.Trigger>

              <ContextMenu.Portal>
                <ContextMenu.Content class="dropdown is-active">
                  <div class="dropdown-menu">
                    <div class="dropdown-content">
                      <ContextMenu.Item
                        as="a"
                        class="dropdown-item"
                        classList={{ "is-disabled": !props.badge.printed }}
                        disabled={!props.badge.printed}
                        onClick={promptClearPrint}
                      >
                        Clear Print
                      </ContextMenu.Item>

                      <ContextMenu.Separator class="dropdown-divider" />

                      <ContextMenu.Item
                        as="a"
                        class="dropdown-item"
                        onClick={() => create(true, false)}
                      >
                        New Basic
                      </ContextMenu.Item>
                      <ContextMenu.Item
                        as="a"
                        class="dropdown-item"
                        onClick={() => create(false, false)}
                      >
                        New Clone
                      </ContextMenu.Item>

                      <Show when={config.terminals.selected?.features.prompt}>
                        <ContextMenu.Item
                          as="a"
                          class="dropdown-item"
                          onClick={() => create(true, true)}
                        >
                          Prompt Basic
                        </ContextMenu.Item>
                        <ContextMenu.Item
                          as="a"
                          class="dropdown-item"
                          onClick={() => create(false, true)}
                        >
                          Prompt Clone
                        </ContextMenu.Item>
                      </Show>
                    </div>
                  </div>
                </ContextMenu.Content>
              </ContextMenu.Portal>
            </ContextMenu>
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
    </div>
  );
};
