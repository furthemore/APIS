import {
  Accessor,
  Component,
  type JSX,
  createSignal,
  splitProps,
} from "solid-js";

import { CartManager } from "../cart/cart-manager";

export type AttendeeDetails = {
  firstName?: string;
  lastName?: string;
  preferredName?: string;
  email?: string;
  phone?: string;
  address1?: string;
  address2?: string;
  city?: string;
  state?: string;
  country?: string;
  postalCode?: string;
  dob?: string;
};

export const DisplayRegistrationButton: Component<
  {
    children: JSX.Element;
    cartManager: CartManager;
    details?: Accessor<AttendeeDetails>;
  } & JSX.IntrinsicElements["button"]
> = (props) => {
  const [customProps, buttonProps] = splitProps(props, [
    "children",
    "cartManager",
    "details",
  ]);

  const [isLoading, setIsLoading] = createSignal(false);

  const display = async () => {
    setIsLoading(true);
    customProps.cartManager.displayRegistration(customProps.details?.() || {});
    setIsLoading(false);
  };

  return (
    <button
      type="button"
      {...buttonProps}
      classList={{ "is-loading": isLoading() }}
      onClick={() => display()}
    >
      {customProps.children}
    </button>
  );
};
