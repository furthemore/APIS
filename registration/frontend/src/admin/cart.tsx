import { Accessor, Component, createSignal, For, Setter, Show } from "solid-js";
import { render } from "solid-js/web";

import { ApisConfig, ApisUrls } from "../entrypoints/admin";

const CSRF_TOKEN = document.querySelector<HTMLMetaElement>(
  "meta[name='csrf_token']"
).content;

export let cartManager: CartManager | null = null;
const [cartEntries, setCartEntries] = createSignal<CartResponse | null>(null);

class CartManager {
  urls: ApisUrls;
  cartEntries: Accessor<CartResponse>;
  setCartEntries: Setter<CartResponse>;

  constructor(
    urls: ApisUrls,
    cartEntries: Accessor<CartResponse>,
    setCartEntries: Setter<CartResponse>
  ) {
    this.urls = urls;
    this.cartEntries = cartEntries;
    this.setCartEntries = setCartEntries;
  }

  updateCart(data: CartResponse) {
    if (!data.success) {
      alert("Failed to update cart");
      window.location.reload();
      return;
    }

    this.setCartEntries(data);
  }

  async addCartId(id: string) {
    let url = new URL(this.urls.onsite_add_to_cart, window.location.href);
    url.search = new URLSearchParams({ id: id.toString() }).toString();

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    await resp.json();

    await this.refreshCart();
  }

  async clearCart() {
    const resp = await fetch(this.urls.onsite_admin_clear_cart, {
      method: "POST",
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    await resp.json();

    this.setCartEntries(null);
  }

  async refreshCart() {
    const resp = await fetch(this.urls.onsite_admin_cart, {
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    const data = await resp.json();

    this.updateCart(data);
  }
}

interface FallibleResponse {
  success: boolean;
}

interface CartResponse extends FallibleResponse {
  charityDonation: string;
  order_id: number;
  orgDonation: string;
  reference: string;
  subtotal: string;
  total: string;
  total_discount: string;
  result: Badge[];
}

interface Badge {
  abandoned: string;
  age: number;
  badgeName: string;
  badgeNumber: number | null;
  firstName: string;
  lastName: string;
  holdType: string | null;
  printed: boolean;
  effectiveLevel: EffectiveLevel;
  discount: null;
  level_subtotal: string;
  level_discount: string;
  level_total: string;
}

interface EffectiveLevel {
  name: string;
  price: string;
}

function Cart(cartManager: CartManager) {
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
                cartManager.refreshCart();
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
            onClick={() => cartManager.clearCart()}
          >
            Clear
          </button>
        </div>
      </div>

      <Show when={cartEntries()}>
        <CartEntries cart={cartEntries()} />
      </Show>
    </div>
  );
}

const CartEntries: Component<{ cart: CartResponse }> = (props) => {
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
        {(badge, index) => <CartBadge data-index={index} badge={badge} />}
      </For>
    </>
  );
};

const CartBadge: Component<{ badge: Badge }> = (props) => {
  return (
    <div class="panel panel-default">
      <div class="panel-heading">
        <span
          classList={{
            label: true,
            "label-success": props.badge.abandoned === "Paid",
            "label-info": props.badge.abandoned === "Comp",
            "label-warning": !["Paid", "Comp"].includes(props.badge.abandoned),
          }}
        >
          {props.badge.abandoned}
        </span>

        <Show when={props.badge.holdType}>
          <span class="label label-danger">{props.badge.holdType}</span>
        </Show>

        <Show when={props.badge.printed}>
          <span class="label label-danger" title="Already printed">
            <i class="fas fa-print" />
          </span>
        </Show>
      </div>

      <table class="table">
        <thead>
          <tr>
            <th>Badge Name</th>
            <th>Level</th>
            <th>Price</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{props.badge.badgeName}</td>
            <td>{props.badge.effectiveLevel?.name || ""}</td>
            <td>{props.badge.effectiveLevel?.price || "0.00"}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default function renderCart(config: ApisConfig) {
  cartManager = new CartManager(config.urls, cartEntries, setCartEntries);
  window["cartManager"] = cartManager;

  render(() => Cart(cartManager), document.getElementById("cart"));
}
