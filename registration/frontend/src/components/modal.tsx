import { Dialog } from "@kobalte/core/dialog";
import { createMediaQuery } from "@solid-primitives/media";
import { createPresence } from "@solid-primitives/presence";
import { type Accessor, type Component, type JSX } from "solid-js";

const MODAL_TRANSITION_TIME_MS = 300;

export const Modal: Component<{
  children: JSX.Element;
  trigger?: () => JSX.Element;
  open: Accessor<boolean>;
  onOpenChange: (open: boolean) => void;
}> = (props) => {
  const prefersReducedMotion = createMediaQuery(
    "(prefers-reduced-motion: reduce)",
  );

  const { isVisible, isMounted } = createPresence(() => props.open(), {
    transitionDuration: () =>
      prefersReducedMotion() ? 0 : MODAL_TRANSITION_TIME_MS,
  });

  return (
    <Dialog open={isMounted()} onOpenChange={props.onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay
          class="modal-backdrop fade"
          classList={{ show: isVisible() }}
        />
      </Dialog.Portal>

      {props.trigger?.()}

      <Dialog.Content
        class="modal fade d-block"
        classList={{ show: isVisible() }}
      >
        {props.children}
      </Dialog.Content>
    </Dialog>
  );
};
