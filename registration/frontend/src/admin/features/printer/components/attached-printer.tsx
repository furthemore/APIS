import { type Component, Show } from "solid-js";

import type { PrintProgress } from "..";

export const AttachedPrinter: Component<{
  device: USBDevice;
  isConnected: boolean;
  error: any;
  progress: PrintProgress | null;
  onForget: () => void;
}> = (props) => {
  return (
    <div
      class="card"
      classList={{
        "border-success": props.isConnected,
        "border-warning": !props.isConnected,
      }}
    >
      <div class="card-header">{props.device.productName}</div>
      <div class="card-body mb-0">
        <Show when={props.error}>
          <div class="alert alert-danger">Error: {props.error.toString()}</div>
        </Show>

        <Show
          when={props.progress}
          fallback={
            <button class="btn btn-danger btn-sm" onClick={props.onForget}>
              Forget
            </button>
          }
        >
          {(progress) => (
            <div class="progress" style={{ height: "1.5rem" }}>
              <Show
                when={progress().total}
                fallback={
                  <div
                    class="progress-bar progress-bar-striped progress-bar-animated w-100"
                    role="progressbar"
                  >
                    Printing...
                  </div>
                }
              >
                {(total) => {
                  const pct = () =>
                    Math.round((progress().sent / total()) * 100);
                  return (
                    <div
                      class="progress-bar progress-bar-striped progress-bar-animated"
                      role="progressbar"
                      style={{ width: `${pct()}%` }}
                      aria-valuenow={progress().sent}
                      aria-valuemin={0}
                      aria-valuemax={total()}
                    >
                      {pct()}%
                    </div>
                  );
                }}
              </Show>
            </div>
          )}
        </Show>
      </div>
    </div>
  );
};
