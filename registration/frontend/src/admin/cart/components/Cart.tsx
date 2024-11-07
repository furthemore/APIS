import { Show } from "solid-js/web";
import { Component, createEffect } from "solid-js";

import { CartManager, CartResponse } from "../cart-manager";
import { CartEntries } from "./CartEntries";
import { CartActions } from "./CartActions";

export const Cart: Component<{
  cartManager: CartManager;
  cartEntries: CartResponse;
}> = (props) => {
  createEffect(() => {
    props.cartManager.refreshCart();
  });

  return (
    <div class="col-md-6">
      <div class="row">
        <div class="col-md-8">
          <h2>
            Cart&nbsp;
            <a
              href="#"
              onClick={(ev) => {
                ev.preventDefault();
                props.cartManager.refreshCart();
              }}
              style={"font-size: 50%;"}
            >
              <i class="fas fa-sync"></i>
              <span class="sr-only">Refresh</span>
            </a>
          </h2>
        </div>
        <div class="col-md-4">
          <button
            class="btn btn-danger right"
            onClick={() => props.cartManager.clearCart()}
          >
            Clear
          </button>
        </div>
      </div>

      <Show when={props.cartEntries}>
        <CartEntries manager={props.cartManager} cart={props.cartEntries} />
      </Show>

      <CartActions
        manager={props.cartManager}
        cartEntries={props.cartEntries}
      />
    </div>
  );
};
