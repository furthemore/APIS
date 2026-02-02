import { Accessor, Setter, createSignal } from "solid-js";

import { ApisUrls } from "../../entrypoints/admin";
import { FallibleRequest, api } from "../api";
import { AttendeeDetails } from "../components/DisplayRegistration";
import MqttClient from "../mqtt";

const LOCK_NAME = "onsite-cart-update";

export class CartManager {
  private urls: ApisUrls;
  private mqtt: MqttClient;

  public cartEntries: Accessor<CartResponse | undefined>;
  private setCartEntries: Setter<CartResponse | undefined>;

  public pendingTransfers: Accessor<number[][]>;
  private setPendingTransfers: Setter<number[][]>;

  constructor(urls: ApisUrls, mqtt: MqttClient) {
    this.urls = urls;
    this.mqtt = mqtt;

    [this.cartEntries, this.setCartEntries] = createSignal<CartResponse>();
    [this.pendingTransfers, this.setPendingTransfers] = createSignal<
      number[][]
    >([], {
      equals: false,
    });

    this.mqtt.emitter.on("refresh", this.refreshCart.bind(this));
    this.mqtt.emitter.on("transfer", this.addPendingTransfer.bind(this));
    this.mqtt.emitter.on(
      "registration/completed",
      this.completedRegistration.bind(this),
    );
  }

  close() {
    this.mqtt.emitter.off("refresh", this.refreshCart.bind(this));
    this.mqtt.emitter.off("transfer", this.addPendingTransfer.bind(this));
    this.mqtt.emitter.off(
      "registration/completed",
      this.completedRegistration.bind(this),
    );
  }

  private completedRegistration(payload: object | null) {
    const badgeId =
      payload && "badgeId" in payload && (payload["badgeId"] as number);
    if (badgeId) {
      this.addCartId(badgeId);
    }
  }

  private addPendingTransfer(payload: object | null) {
    const data = payload as { badgeIds: number[] };

    let pendingTransfers = this.pendingTransfers();
    pendingTransfers.push(data.badgeIds);
    this.setPendingTransfers(pendingTransfers);
  }

  public getNextTransfer(): number[] | undefined {
    let pendingTransfers = this.pendingTransfers();
    const nextTransfer = pendingTransfers.shift();
    this.setPendingTransfers(pendingTransfers);
    return nextTransfer;
  }

  private async makeRequest<T>(
    input: string | URL,
    init?: RequestInit,
  ): Promise<FallibleRequest<T>> {
    const perform = async () => {
      const data = await api(input, init).json<FallibleRequest<T>>();
      console.debug("Got response data", data);
      return data;
    };

    if ("locks" in navigator && navigator.locks) {
      return await navigator.locks.request(LOCK_NAME, perform);
    } else {
      console.warn("Locks unavailable, session data might get out of sync!");
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
      this.urls.onsite_admin_cart,
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
    tendered: string,
  ): Promise<FallibleRequest<void>> {
    let url = new URL(
      this.urls.complete_cash_transaction,
      window.location.href,
    );
    url.searchParams.set("reference", reference);
    url.searchParams.set("total", total);
    url.searchParams.set("tendered", tendered);

    const data = await this.makeRequest(url, {
      method: "POST",
    });

    return data;
  }

  public async enableCardPayment(
    fallback: boolean,
  ): Promise<FallibleRequest<void>> {
    let url = new URL(this.urls.enable_payment, window.location.href);
    if (fallback) url.searchParams.set("fallback", "true");

    return await this.makeRequest(url);
  }

  public async printBadges(
    ids: number[],
    clearCart: boolean = true,
    mqttPrint: boolean = false,
    beforeClearingCart?: () => void,
  ): Promise<FallibleRequest<BadgePrintResponse>> {
    const assignData = await this.makeRequest(this.urls.assign_badge_number, {
      method: "POST",
      body: JSON.stringify(
        ids.map((id) => {
          return {
            id,
          };
        }),
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

      this.mqtt.publishPrintMessage(JSON.stringify({ url }));

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
      window.location.href,
    );
    url.pathname = url.pathname.replace("0", id.toString());
    return url.toString();
  }

  public alreadyInCart(id: number): boolean {
    return (
      this.cartEntries()?.result?.some((badge) => badge.id === id) || false
    );
  }

  public async createAndApplyDiscount(
    amount: string,
  ): Promise<FallibleRequest<void>> {
    const formData = new FormData();
    formData.set("amount", amount);

    return await this.makeRequest(this.urls.onsite_create_discount, {
      method: "POST",
      body: formData,
    });
  }

  public async printReceipts(): Promise<FallibleRequest<void>> {
    if (!this.cartEntries()?.result) {
      return { success: true } as FallibleRequest<void>;
    }

    let url = new URL(this.urls.onsite_print_receipts, window.location.href);
    this.cartEntries()?.result?.forEach((badge) =>
      url.searchParams.append("reference", badge.reference),
    );

    return await this.makeRequest(url);
  }

  public async transfer(terminal_id: number): Promise<FallibleRequest<void>> {
    if (!this.cartEntries()?.result) {
      return { success: true } as FallibleRequest<void>;
    }

    let url = new URL(
      this.urls.onsite_admin_transfer_cart,
      window.location.href,
    );
    url.searchParams.append("terminal_id", terminal_id.toString());
    this.cartEntries()?.result?.forEach((badge) => {
      url.searchParams.append("badge_id", badge.id.toString());
    });

    const resp = await this.makeRequest(url);
    if (!resp.success) {
      return resp;
    }

    await this.clearCart();

    return { success: true } as FallibleRequest<void>;
  }

  public getOnsiteUrl(details: AttendeeDetails): URL {
    const regUrl = new URL(this.urls.onsite, window.location.href);
    Object.entries(details).forEach(([name, value]) => {
      regUrl.searchParams.set(name, value);
    });
    return regUrl;
  }

  public async displayRegistration(
    details: AttendeeDetails,
  ): Promise<FallibleRequest<void>> {
    let url = new URL(this.urls.onsite_regtoken, window.location.href);
    const resp = await api.post(url).json<FallibleRequest<{ token: String }>>();
    if (!resp.success) {
      return resp;
    }

    const regUrl = this.getOnsiteUrl(details);

    this.mqtt.publishMessage(
      "payment/registration/display",
      JSON.stringify({
        url: regUrl.toString(),
        token: resp.token,
      }),
    );
  }

  public cancelRegistration() {
    this.mqtt.publishMessage("payment/registration/cancel", JSON.stringify({}));
  }

  public async fetchAttendeeDetails(
    badgeId: number,
  ): Promise<FallibleRequest<{ attendee: AttendeeDetails }>> {
    return await api
      .get(this.urls.onsite_attendee_details, {
        searchParams: { id: badgeId },
      })
      .json();
  }
}

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
  reference: string;
  staff?: Staff;
}

export interface EffectiveLevel {
  name: string;
  price: string;
}

export interface Discount {
  name: string;
  amount_off: string;
  percent_off: number;
  reason?: string;
}

export interface AttendeeOption {
  quantity: number;
  item: string;
  price: string;
  total: string;
  reason?: string;
  optionExtraType?: "int" | "bool" | "string" | "ShirtSizes";
  optionValue?: string;
}

export interface Staff {
  shirtSize: string;
}

export interface BadgePrintResponse {
  file: string;
  next: string;
  url: string;
}
