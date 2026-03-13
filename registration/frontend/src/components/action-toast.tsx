import { Toast, type ToastComponentProps } from "@kobalte/core/toast";
import { type Component, createSignal, onMount, splitProps } from "solid-js";

export type ActionToastType = "success" | "warning" | "danger";

export type ActionToastProps = {
  type: ActionToastType;
  message: string;
} & ToastComponentProps;

export const ActionToast: Component<ActionToastProps> = (props) => {
  const [actionProps, toastProps] = splitProps(props, ["type", "message"]);

  const [showToast, setShowToast] = createSignal(false);

  onMount(() => {
    setShowToast(true);
  });

  const typeClasses = () =>
    ({
      success: "text-bg-success",
      warning: "text-bg-warning",
      danger: "text-bg-danger",
    })[props.type];

  return (
    <Toast
      as="div"
      class={`toast fade show align-items-center border-0 ${typeClasses()}`}
      classList={{
        showing: !showToast(),
      }}
      {...toastProps}
    >
      <div class="d-flex">
        <Toast.Title class="toast-body">{actionProps.message}</Toast.Title>
        <Toast.CloseButton class="btn-close btn-close-white m-auto me-2" />
      </div>
    </Toast>
  );
};
