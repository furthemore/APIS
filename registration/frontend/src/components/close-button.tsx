import { type Component } from "solid-js";

export const CloseButton: Component<{ close(): void }> = (props) => {
  return (
    <button
      type="button"
      class="btn-close"
      aria-label="Close"
      onClick={() => props.close()}
    />
  );
};
