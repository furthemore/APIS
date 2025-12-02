import { Dialog } from "@kobalte/core/dialog";
import { createMediaQuery } from "@solid-primitives/media";
import { createPresence } from "@solid-primitives/presence";
import {
  type Accessor,
  type Component,
  type JSX,
  type Setter,
  createEffect,
  createSignal,
} from "solid-js";

const MODAL_TRANSITION_TIME_MS = 300;

export type ModalSignal = [Accessor<boolean>, Setter<boolean>];

export const Modal: Component<{
  children: JSX.Element;
  trigger?: () => JSX.Element;
  signal?: ModalSignal;
}> = (props) => {
  const prefersReducedMotion = createMediaQuery(
    "(prefers-reduced-motion: reduce)",
  );

  const [showModal, setShowModal] = createSignal(false);

  createEffect(() => props.signal && setShowModal(props.signal[0]));
  createEffect(() => props.signal && props.signal[1](showModal()));

  const { isVisible, isMounted } = createPresence(showModal, {
    transitionDuration: () =>
      prefersReducedMotion() ? 0 : MODAL_TRANSITION_TIME_MS,
  });

  return (
    <Dialog open={isMounted()} onOpenChange={setShowModal}>
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
