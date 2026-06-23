import { HidPosDevice, SnapiDevice } from "@syfaro/scanners-and-such-web";
import {
  type Component,
  Show,
  createEffect,
  createResource,
  createSignal,
  onCleanup,
} from "solid-js";

import { type DeviceDriver, driverNameForDevice } from "..";

export const AttachedDevice: Component<{
  device: HIDDevice;
  triggerRefresh: () => void;
  emitRawScan: (value: string) => void;
}> = (props) => {
  const [connected, setConnected] = createSignal(true);

  const processValue = (emit: (value: string) => void, value: Uint8Array) =>
    emit(new TextDecoder("utf-8").decode(value));

  const [device] = createResource<
    DeviceDriver | undefined,
    [HIDDevice, (value: string) => void, boolean],
    DeviceDriver | undefined
  >(
    (): [HIDDevice, (value: string) => void, boolean] => [
      props.device,
      props.emitRawScan,
      connected(),
    ],
    async ([device, emit, connected], { value }) => {
      if (value) {
        await value.close();
      }

      if (import.meta.env.DEV) {
        // Hot reload doesn't wait for disconnect and we can only open the
        // device once.
        while (device.opened) {
          await new Promise((resolve) => setTimeout(resolve, 100));
        }
      }

      if (!connected) return;

      const driverName = driverNameForDevice(device);
      if (!driverName) return;

      let driver;
      if (driverName === "snapi") {
        driver = new SnapiDevice();
        driver.start(device, (data) => {
          if (data.type === "barcode") {
            processValue(emit, data.value.data);
          }
        });
      } else if (driverName === "usb-hid") {
        driver = new HidPosDevice();
        driver.start(device, (data) => {
          processValue(emit, data.value);
        });
      }

      return driver;
    },
  );

  createEffect(() => {
    if (!connected() && props.device.opened) {
      device.latest?.close();
    }
  });

  onCleanup(() => {
    if (props.device.opened) {
      device.latest?.close();
    }
  });

  const forget = async () => {
    await props.device.forget();
    props.triggerRefresh();
  };

  return (
    <div
      class="card"
      classList={{
        "border-success": connected(),
        "border-warning": !connected(),
      }}
    >
      <div class="card-header">{props.device.productName}</div>
      <div class="card-body mb-0">
        <Show
          when={connected()}
          fallback={
            <button
              class="btn btn-info btn-sm me-1"
              onClick={[setConnected, true]}
            >
              Connect
            </button>
          }
        >
          <button
            class="btn btn-warning btn-sm me-1"
            onClick={[setConnected, false]}
          >
            Disconnect
          </button>
        </Show>

        <button class="btn btn-danger btn-sm me-1" onClick={forget}>
          Forget
        </button>
      </div>
    </div>
  );
};
