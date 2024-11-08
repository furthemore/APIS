import { Accessor, createSignal, Setter } from "solid-js";

import { ApisUrls, CSRF_TOKEN } from "../../entrypoints/admin";
import MqttClient from "../mqtt";

export class CartManager {
  private urls: ApisUrls;
  private mqtt: MqttClient;

  public cartEntries: Accessor<CartResponse>;
  private setCartEntries: Setter<CartResponse>;

  constructor(urls: ApisUrls, mqtt: MqttClient) {
    this.urls = urls;

    const [cartEntries, setCartEntries] = createSignal<CartResponse>();
    this.cartEntries = cartEntries;
    this.setCartEntries = setCartEntries;

    this.mqtt = mqtt;
    mqtt.emitter.on("refresh", this.refreshCart.bind(this));
  }

  close() {
    this.mqtt.emitter.off("refresh", this.refreshCart.bind(this));
  }

  private updateCart(data: FallibleRequest<CartResponse>) {
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
  ): Promise<FallibleRequest<void>> {
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

  public async enableCardPayment(): Promise<FallibleRequest<void>> {
    const resp = await fetch(this.urls.enable_payment, {
      headers: {
        "x-csrftoken": CSRF_TOKEN,
      },
    });
    const data = await resp.json();

    return data;
  }

  public async printBadges(
    ids: number[],
    mqttPrint: boolean = false
  ): Promise<FallibleRequest<BadgePrintResponse>> {
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
    const assignData: FallibleRequest<void> = await assignResp.json();

    if (!assignData.success) {
      return { success: false };
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
    const printData: FallibleRequest<BadgePrintResponse> =
      await printResp.json();

    if (printData.success && mqttPrint) {
      console.debug(`Wants MQTT print for ${printData.file}`);

      let url = new URL(this.urls.pdf, window.location.href);
      url.searchParams.append("file", printData.file);

      this.mqtt.publishMessage(
        "action",
        JSON.stringify({
          action: "print",
          url,
        })
      );
    } else {
      console.debug("Not using MQTT print");
    }

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

  public alreadyInCart(id: number): boolean {
    return (
      this.cartEntries()?.result?.some((badge) => badge.id === id) || false
    );
  }
}

export type FallibleRequest<T> =
  | {
      success: false;
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
