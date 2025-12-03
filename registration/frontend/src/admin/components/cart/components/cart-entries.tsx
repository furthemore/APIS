import { faSackDollar, faShirt } from "@fortawesome/free-solid-svg-icons";
import Fa from "solid-fa";
import {
  type Component,
  For,
  Match,
  Show,
  Switch,
  createMemo,
  createSelector,
  createSignal,
  useContext,
} from "solid-js";

import type {
  AttendeeOption,
  CartResponse,
  OnsiteAdminContext,
} from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";
import { UserSettingsContext } from "@admin/providers/user-settings-provider";

import { cleanMoneyAmount } from "../utils";
import { CartBadge } from "./cart-badge";

export const CartEntries: Component<{
  entries?: CartResponse;
}> = (props) => {
  const userSettings = useContext(UserSettingsContext)!;

  const [hoveredOrderId, setHoveredOrderId] = createSignal<number>();
  const hoveredOrderIdSelector = createSelector(hoveredOrderId);

  const orderItems = createMemo(() =>
    props.entries?.result
      .flatMap((result) => {
        const options = result.attendee_options;
        if (result.discount) {
          let price;

          if (result.discount.percent_off > 0) {
            price = `-${result.discount.percent_off}%`;
          } else {
            price = `-$${result.discount.amount_off}`;
          }

          options.push({
            quantity: 1,
            price,
            item: `Discount ${result.discount.name}`,
            total: `-${cleanMoneyAmount(result.level_discount)}`,
            reason: result.discount.reason,
          });
        }
        return options;
      })
      .flat(),
  );

  return (
    <>
      <Show when={(orderItems()?.length || 0) > 0}>
        <div class="card-body pt-0">
          <div class="card flush-table">
            <div class="card-header">
              <Fa icon={faShirt} fw class="me-1" />
              Items
            </div>

            <div class="card-body py-0">
              <table class="table-sm table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th style={{ width: "20%" }}>Price</th>
                  </tr>
                </thead>
                <tbody>
                  <For
                    each={orderItems()?.filter(
                      (orderItem) => orderItem.quantity > 0,
                    )}
                  >
                    {(item) => (
                      <tr>
                        <AttendeeOptionDescription item={item} />
                        <td>
                          <span>{cleanMoneyAmount(item.total)}</span>
                        </td>
                      </tr>
                    )}
                  </For>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Show>

      <Show when={(props.entries?.result.length || 0) > 0}>
        <div class="card-body py-0">
          <div
            class="row row-cols-1 g-2 mb-3"
            classList={{
              "row-cols-xl-2": userSettings().settings().multipleBadgeColumns,
            }}
          >
            <For each={props.entries!.result}>
              {(badge) => (
                <div
                  class="col"
                  onMouseEnter={[setHoveredOrderId, badge.orderId]}
                  onMouseLeave={[setHoveredOrderId, undefined]}
                >
                  <CartBadge
                    badge={badge}
                    hoveredOrderIdSelector={hoveredOrderIdSelector}
                  />
                </div>
              )}
            </For>
          </div>
        </div>
      </Show>

      <div class="card-body pt-0">
        <div class="card flush-table">
          <div class="card-header">
            <Fa icon={faSackDollar} fw class="me-1" />
            Price
          </div>

          <div class="card-body py-0">
            <table class="table-sm table">
              <tbody>
                <tr>
                  <td>Subtotal:</td>
                  <td style={{ width: "20%" }}>
                    {cleanMoneyAmount(props.entries?.subtotal)}
                  </td>
                </tr>
                <tr>
                  <td>Discounts:</td>
                  <td>{cleanMoneyAmount(props.entries?.total_discount)}</td>
                </tr>
                <tr>
                  <td>Donation to Charity:</td>
                  <td>{cleanMoneyAmount(props.entries?.charityDonation)}</td>
                </tr>
                <tr>
                  <td>Donation to Convention:</td>
                  <td>{cleanMoneyAmount(props.entries?.orgDonation)}</td>
                </tr>
                <tr class="has-text-weight-semibold">
                  <td>Total:</td>
                  <td>{cleanMoneyAmount(props.entries?.total)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
};

const AttendeeOptionDescription: Component<{ item: AttendeeOption }> = (
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
                {getShirtSizeName(config, props.item.optionValue)}
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

function getShirtSizeName(
  config: OnsiteAdminContext,
  optionValue?: string,
): string | undefined {
  if (!optionValue) return;

  const sizeName = config.shirtSizes.find(
    (entry) => entry.id === parseInt(optionValue, 10),
  )?.name;

  return sizeName || optionValue;
}
