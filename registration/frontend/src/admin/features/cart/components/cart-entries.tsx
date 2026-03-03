import { faSackDollar } from "@fortawesome/free-solid-svg-icons";
import Fa from "solid-fa";
import {
  type Component,
  For,
  Show,
  createSelector,
  createSignal,
  useContext,
} from "solid-js";

import type { CartResponse } from "@admin/api";
import { UserSettingsContext } from "@admin/providers/user-settings-provider";

import { cleanMoneyAmount } from "../utils";
import { CartBadge } from "./cart-badge";

export const CartEntries: Component<{
  entries?: CartResponse;
}> = (props) => {
  const userSettings = useContext(UserSettingsContext)!;

  const [hoveredOrderId, setHoveredOrderId] = createSignal<number>();
  const hoveredOrderIdSelector = createSelector(hoveredOrderId);

  return (
    <>
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
                  role="none"
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
        <div class="row row-cols-1 g-2 row-cols-xl-2">
          <div class="col order-2 order-xl-1">
            <div class="card flush-table h-100">
              <div class="card-header">
                <Fa icon={faSackDollar} fw class="me-1" />
                Price
              </div>

              <div class="card-body py-0">
                <table class="table-sm table">
                  <thead class="visually-hidden">
                    <tr>
                      <th>Type</th>
                      <th>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Subtotal</td>
                      <td class="text-end">
                        {cleanMoneyAmount(props.entries?.subtotal)}
                      </td>
                    </tr>
                    <tr>
                      <td>Discounts</td>
                      <td class="text-end">
                        {cleanMoneyAmount(props.entries?.total_discount)}
                      </td>
                    </tr>
                    <tr>
                      <td>Donation to Charity</td>
                      <td class="text-end">
                        {cleanMoneyAmount(props.entries?.charityDonation)}
                      </td>
                    </tr>
                    <tr>
                      <td>Donation to Convention</td>
                      <td class="text-end">
                        {cleanMoneyAmount(props.entries?.orgDonation)}
                      </td>
                    </tr>
                    <tr class="fw-semibold">
                      <td>Total</td>
                      <td class="text-end">
                        {cleanMoneyAmount(props.entries?.total)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
