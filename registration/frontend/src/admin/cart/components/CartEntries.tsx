import { Component, createMemo, For, Show } from "solid-js";

import { CartManager, CartResponse } from "../cart-manager";
import { CartBadge } from "./CartBadge";

export const CartEntries: Component<{
  manager: CartManager;
  cart: CartResponse;
}> = (props) => {
  const orderItems = createMemo(() =>
    props.cart.result
      .flatMap((result) => {
        let options = result.attendee_options;
        if (result.discount) {
          options.push({
            quantity: 1,
            item: `Discount ${result.discount.name}`,
            price: `-${result.discount.amount_off} / ${result.discount.percent_off}%`,
            total: `-$${result.level_discount}`,
          });
        }
        return options;
      })
      .flat()
  );

  return (
    <>
      <div class="total">
        <table class="total-table">
          <tbody>
            <tr>
              <td>Subtotal:</td>
              <td>{props.cart.subtotal}</td>
            </tr>
            <tr>
              <td>Discounts:</td>
              <td>{props.cart.total_discount}</td>
            </tr>
            <tr>
              <td>Donation to Charity:</td>
              <td>{props.cart.charityDonation}</td>
            </tr>
            <tr>
              <td>Donation to Convention:</td>
              <td>{props.cart.orgDonation}</td>
            </tr>
            <tr>
              <td>
                <b>Total:</b>
              </td>
              <td class="success">{`${props.cart.total}`}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <For each={props.cart.result}>
        {(badge, index) => (
          <CartBadge
            data-index={index()}
            manager={props.manager}
            badge={badge}
          />
        )}
      </For>

      <Show when={orderItems()?.length > 0}>
        <div class="panel panel-default">
          <table class="table">
            <thead>
              <tr>
                <th>Order Item</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              <For each={orderItems()}>
                {(item, index) => (
                  <tr data-index={index()}>
                    <td>{`${item.quantity} × ${item.item} (@ ${item.price})`}</td>
                    <td>
                      <span>{item.total}</span>
                    </td>
                  </tr>
                )}
              </For>
            </tbody>
          </table>
        </div>
      </Show>
    </>
  );
};
