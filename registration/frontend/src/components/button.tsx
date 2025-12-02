import { Button as KobalteButton } from "@kobalte/core/button";
import { type Component, type JSX, splitProps } from "solid-js";

export type ButtonProps = {
  children: JSX.Element;
  loading?: boolean;
} & JSX.IntrinsicElements["button"];

export const Button: Component<ButtonProps> = (props) => {
  const [customProps, buttonProps] = splitProps(props, ["loading", "children"]);

  const disabled = () => customProps.loading || buttonProps.disabled;

  return (
    <KobalteButton
      {...buttonProps}
      class={`btn-loader ${buttonProps.class || ""}`}
      disabled={disabled()}
      aria-busy={customProps.loading}
    >
      <span class="content">{customProps.children}</span>
      <span class="spinner">
        <span class="spinner-border spinner-border-sm" aria-hidden="true" />
        <span class="visually-hidden" role="status">
          Loading...
        </span>
      </span>
    </KobalteButton>
  );
};
