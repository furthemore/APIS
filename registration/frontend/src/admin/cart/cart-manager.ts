import { Accessor, createSignal, Setter } from "solid-js";

import { ApisUrls, CSRF_TOKEN } from "../../entrypoints/admin";
import MqttClient from "../mqtt";

const LOCK_NAME = "onsite-cart-update";

export class CartManager {
  private urls: ApisUrls;
  private mqtt: MqttClient;

  public cartEntries: Accessor<CartResponse | undefined>;
  private setCartEntries: Setter<CartResponse | undefined>;

  constructor(urls: ApisUrls, mqtt: MqttClient) {
    this.urls = urls;
    this.mqtt = mqtt;

    [this.cartEntries, this.setCartEntries] = createSignal<CartResponse>();

    this.mqtt.emitter.on("refresh", this.refreshCart.bind(this));
  }

  close() {
    this.mqtt.emitter.off("refresh", this.refreshCart.bind(this));
  }

  private async makeRequest<T>(
    input: string | URL,
    init?: RequestInit
  ): Promise<FallibleRequest<T>> {
    const perform = async () => {
      console.debug("Making request", input);
      const resp = await fetch(input, {
        ...init,
        headers: { "x-csrftoken": CSRF_TOKEN, ...init?.headers },
      });
      const data = await resp.json();
      console.debug("Got response data", input, data);
      return data;
    };
    if ("locks" in navigator && navigator.locks) {
      console.debug("Aquiring cart update lock for request", input);
      return await navigator.locks.request(LOCK_NAME, perform);
    } else {
      console.warn("locks unavailable, session data might get out of sync!");
      return await perform();
    }
  }

  public async addCartId(id: number) {
    let url = new URL(this.urls.onsite_add_to_cart, window.location.href);
    url.searchParams.set("id", id.toString());

    await this.makeRequest(url, {
      method: "POST",
    });

    await this.refreshCart();
  }

  public async clearCart() {
    await this.makeRequest(this.urls.onsite_admin_clear_cart, {
      method: "POST",
    });

    this.setCartEntries(undefined);
  }

  public async refreshCart() {
    const data = await this.makeRequest<CartResponse>(
      this.urls.onsite_admin_cart
    );

    if (!data.success) {
      console.error("Failed to update cart", data);
      alert("Failed to update cart");
      window.location.reload();
      return;
    }

    this.setCartEntries(data);
  }

  public async removeBadge(id: number) {
    let url = new URL(this.urls.onsite_remove_from_cart, window.location.href);
    url.searchParams.set("id", id.toString());

    const data = await this.makeRequest(url, {
      method: "POST",
    });

    if (!data.success) {
      alert(`Error removing from cart: ${data.reason}`);
      return;
    }

    await this.refreshCart();
  }

  public async applyCashPayment(
    reference: string,
    total: string,
    tendered: string
  ): Promise<FallibleRequest<void>> {
    let url = new URL(
      this.urls.complete_cash_transaction,
      window.location.href
    );
    url.searchParams.set("reference", reference);
    url.searchParams.set("total", total);
    url.searchParams.set("tendered", tendered);

    const data = await this.makeRequest(url, {
      method: "POST",
    });

    return data;
  }

  public async enableCardPayment(): Promise<FallibleRequest<void>> {
    return await this.makeRequest(this.urls.enable_payment);
  }

  public async printBadges(
    ids: number[],
    clearCart: boolean = true,
    mqttPrint: boolean = false,
    beforeClearingCart?: () => void
  ): Promise<FallibleRequest<BadgePrintResponse>> {
    const assignData = await this.makeRequest(this.urls.assign_badge_number, {
      method: "POST",
      body: JSON.stringify(
        ids.map((id) => {
          return {
            id,
          };
        })
      ),
    });

    if (!assignData.success) {
      return { success: false };
    }

    let url = new URL(this.urls.onsite_print_badges, window.location.href);
    ids.forEach((id) => url.searchParams.append("id", id.toString()));

    const printData = await this.makeRequest<BadgePrintResponse>(url);

    if (printData.success && mqttPrint) {
      const url = new URL(printData.file, window.location.href);

      this.mqtt.publishMessage(
        "action",
        JSON.stringify({
          action: "print",
          url,
        })
      );

      if (clearCart) {
        beforeClearingCart?.();
        await this.clearCart();
      }
    }

    return printData;
  }

  public async clearBadgePrinted(id: number): Promise<FallibleRequest<void>> {
    let url = new URL(this.urls.onsite_print_clear, window.location.href);
    url.searchParams.set("id", id.toString());

    return await this.makeRequest(url, {
      method: "POST",
    });
  }

  public urlForBadge(id: number): string {
    let url = new URL(
      this.urls.registration_badge_change,
      window.location.href
    );
    url.pathname = url.pathname.replace("0", id.toString());
    return url.toString();
  }

  public alreadyInCart(id: number): boolean {
    return (
      this.cartEntries()?.result?.some((badge) => badge.id === id) || false
    );
  }
}

export type FallibleRequest<T> =
  | {
      success: false;
      reason?: string;
    }
  | ({ success: true } & T);

export interface CartResponse {
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
  badgeNumber?: number;
  firstName: string;
  lastName: string;
  holdType?: string;
  printed: boolean;
  effectiveLevel: EffectiveLevel;
  discount?: Discount;
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

export interface BadgePrintResponse {
  file: string;
  next: string;
  url: string;
}
