import {
  faChevronDown,
  faChevronLeft,
  faPrint,
} from "@fortawesome/free-solid-svg-icons";
import Fa from "solid-fa";
import {
  type Component,
  Show,
  Suspense,
  createEffect,
  createResource,
  createSignal,
  onCleanup,
  onMount,
  useContext,
} from "solid-js";

import { MqttContext } from "@admin/providers/mqtt-provider";
import { IconAndLabel } from "@components/icon-and-label";

import { type PrintProgress, USB_SUPPORTED, openPrinter, printUrl } from "..";
import { AttachedPrinter } from "./attached-printer";

export const Printer: Component = () => {
  const mqtt = useContext(MqttContext)!;

  const [show, setShow] = createSignal(false);
  const [selectedDevice, setSelectedDevice] = createSignal<USBDevice>();

  const [printer] = createResource(selectedDevice, async (device) => {
    return await openPrinter(device);
  });

  const [printProgress, setPrintProgress] = createSignal<PrintProgress | null>(
    null,
  );
  const [missedPrint, setMissedPrint] = createSignal(false);

  const isConnected = () =>
    printer.state === "ready" && !!printer() && !!selectedDevice();

  const print = async (payload: object | null) => {
    const p = printer();
    if (!p) {
      setMissedPrint(true);
      setShow(true);
      return;
    }
    const url = (payload as { url: string })["url"];
    try {
      await printUrl(p, url, setPrintProgress);
    } finally {
      setPrintProgress(null);
    }
  };

  const connectDevice = async (device: USBDevice) => {
    if (!isConnected()) {
      setSelectedDevice(device);
    }
  };

  createEffect(() => {
    const m = mqtt();
    m?.emitter.on("print", print);
    onCleanup(() => m?.emitter.off("print", print));
  });

  onMount(async () => {
    if (!USB_SUPPORTED) return;

    const devices = await navigator.usb.getDevices();
    if (devices.length === 1) {
      connectDevice(devices[0]);
    } else {
      setShow(true);
    }
  });

  createEffect(() => {
    if (!USB_SUPPORTED) return;

    const onConnect = async (ev: USBConnectionEvent) => {
      // Device can appear before it's ready, give it time to settle.
      await new Promise((resolve) => setTimeout(resolve, 1000));
      connectDevice(ev.device);
    };

    const onDisconnect = (ev: USBConnectionEvent) => {
      if (ev.device === selectedDevice()) {
        setSelectedDevice(undefined);
        setShow(true);
      }
    };

    navigator.usb.addEventListener("connect", onConnect);
    navigator.usb.addEventListener("disconnect", onDisconnect);

    onCleanup(() => {
      navigator.usb.removeEventListener("connect", onConnect);
      navigator.usb.removeEventListener("disconnect", onDisconnect);
    });
  });

  const pair = async () => {
    forget();

    try {
      const device = await navigator.usb.requestDevice({
        filters: [{ vendorId: 0x0a5f }],
      });
      setSelectedDevice(device);
      setShow(false);
    } catch (err) {
      console.error(err);
    }
  };

  const forget = async () => {
    const device = selectedDevice();
    if (device) {
      if (device.opened) {
        await device.close();
      }
      await device.forget();
      setSelectedDevice(undefined);
    }
  };

  return (
    <div class="card mb-3">
      <div class="card-header">
        <h5 class="card-heading mb-0">
          <div class="row align-items-center g-1">
            <div class="col">
              <IconAndLabel children="Local Printer" icon={faPrint} fw />
            </div>

            <div class="col-auto">
              <button
                class="btn btn-sm btn-secondary"
                onClick={() => setShow((val) => !val)}
              >
                <Fa icon={show() ? faChevronDown : faChevronLeft} fw />
              </button>
            </div>
          </div>
        </h5>
      </div>

      <div class="collapse" classList={{ show: show() }}>
        <Show
          when={USB_SUPPORTED}
          fallback={
            <div class="card-body pb-0">
              <div class="alert alert-warning">WebUSB not supported</div>
            </div>
          }
        >
          <Suspense
            fallback={
              <div class="card-body pb-0">
                <p>Connecting to printer...</p>
              </div>
            }
          >
            <Show when={missedPrint()}>
              <div class="card-body pb-0">
                <div class="alert alert-warning alert-dismissible mb-0">
                  <span>Got print request but no printer was connected!</span>

                  <button
                    type="button"
                    class="btn-close"
                    onClick={() => setMissedPrint(false)}
                  />
                </div>
              </div>
            </Show>

            <Show
              when={selectedDevice()}
              fallback={
                <>
                  <p class="card-body pb-0 mb-0">No printer connected</p>

                  <div class="card-body">
                    <button class="btn btn-info" onClick={pair}>
                      Connect Printer
                    </button>
                  </div>
                </>
              }
            >
              {(device) => (
                <div class="card-body">
                  <AttachedPrinter
                    device={device()}
                    isConnected={isConnected()}
                    error={printer.error}
                    progress={printProgress()}
                    onForget={forget}
                  />
                </div>
              )}
            </Show>
          </Suspense>
        </Show>
      </div>
    </div>
  );
};
