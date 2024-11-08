import { Setter } from "solid-js";

import { ApisUrls, CSRF_TOKEN } from "../../entrypoints/admin";
import emitter from "../mqtt";

export class CartManager {
  urls: ApisUrls;
  setCartEntries: Setter<CartResponse>;

  constructor(urls: ApisUrls, setCartEntries: Setter<CartResponse>) {
    this.urls = urls;
    this.setCartEntries = setCartEntries;

    emitter.on("refresh", this.refreshCart.bind(this));
  }

  close() {
    emitter.off("refresh", this.refreshCart.bind(this));
  }

  private updateCart(data: CartResponse) {
    if (!data.success) {
      alert("Failed to update cart");
      window.location.reload();
      return;
    }

    this.setCartEntries(data);
  }

  public async addCartId(id: number) {
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

  public async clearCart() {
    const resp = await fetch(this.urls.onsite_admin_clear_cart, {
      method: "POST",
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    await resp.json();

    this.setCartEntries(null);
  }

  public async refreshCart() {
    const resp = await fetch(this.urls.onsite_admin_cart, {
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    const data = await resp.json();

    this.updateCart(data);
  }

  public async removeBadge(id: number) {
    let url = new URL(this.urls.onsite_remove_from_cart, window.location.href);
    url.search = new URLSearchParams({ id: id.toString() }).toString();

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    const data = await resp.json();

    if (!data["success"]) {
      alert(`Error removing from cart: ${data["reason"]}`);
      return;
    }

    await this.refreshCart();
  }

  public async applyCashPayment(
    reference: string,
    total: string,
    tendered: string
  ): Promise<FallibleRequest> {
    let url = new URL(
      this.urls.complete_cash_transaction,
      window.location.href
    );
    url.search = new URLSearchParams({ reference, total, tendered }).toString();

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    const data = await resp.json();

    return data;
  }

  public async enableCardPayment(): Promise<FallibleRequest> {
    const resp = await fetch(this.urls.enable_payment, {
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    const data = await resp.json();

    return data;
  }

  public async printBadges(
    ids: number[]
  ): Promise<FallibleRequest | BadgePrintResponse> {
    const assignResp = await fetch(this.urls.assign_badge_number, {
      method: "POST",
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
      body: JSON.stringify(
        ids.map((id) => {
          return {
            id,
          };
        })
      ),
    });
    const assignData: FallibleRequest = await assignResp.json();

    if (!assignData.success) {
      return assignData;
    }

    let url = new URL(this.urls.onsite_print_badges, window.location.href);
    let params = new URLSearchParams();
    ids.forEach((id) => params.append("id", id.toString()));
    url.search = params.toString();

    const printResp = await fetch(url, {
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    const printData: BadgePrintResponse = await printResp.json();

    await this.clearCart();
    await this.refreshCart();

    return printData;
  }

  public urlForBadge(id: number): string {
    let url = new URL(
      this.urls.registration_badge_change,
      window.location.href
    );
    url.pathname = url.pathname.replace("0", id.toString());
    return url.toString();
  }
}

export interface FallibleRequest {
  success: boolean;
}

export interface CartResponse extends FallibleRequest {
  charityDonation: string;
  order_id: number;
  orgDonation: string;
  reference: string;
  subtotal: string;
  total: string;
  total_discount: string;
  result: Badge[];
}

export interface Badge {
  id: number;
  abandoned: string;
  age: number;
  badgeName: string;
  badgeNumber: number | null;
  firstName: string;
  lastName: string;
  holdType: string | null;
  printed: boolean;
  effectiveLevel: EffectiveLevel;
  discount: Discount | null;
  level_subtotal: string;
  level_discount: string;
  level_total: string;
  attendee_options: AttendeeOption[];
}

export interface EffectiveLevel {
  name: string;
  price: string;
}

export interface Discount {
  name: string;
  amount_off: string;
  percent_off: string;
}

export interface AttendeeOption {
  quantity: number;
  item: string;
  price: string;
  total: string;
}

export interface BadgePrintResponse extends FallibleRequest {
  file: string;
  next: string;
  url: string;
}
