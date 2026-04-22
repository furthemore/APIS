import {
  faChevronDown,
  faChevronLeft,
  faKeyboard,
} from "@fortawesome/free-solid-svg-icons";
import type { Emitter } from "@solid-primitives/event-bus";
import { decodeBarcode } from "@syfaro/aamva-web";
import mrtd from "mrtd";
import Fa from "solid-fa";
import {
  type Component,
  For,
  Show,
  Suspense,
  createEffect,
  createResource,
  createSignal,
  onCleanup,
} from "solid-js";

import type { BarcodeEmitter } from "@admin/features/onsite";
import type { AddressData, IdData } from "@admin/features/scan";
import { IconAndLabel } from "@components/icon-and-label";

import { HID_SUPPORTED, filterDevices, mrtdDate, requestHidDevice } from "..";
import { AttachedDevice } from "./attached-device";

const decodeAamva = (value: string): IdData => {
  const data = decodeBarcode(value);

  const id: IdData = {
    documentType: "AAMVA",
    first: data.name?.first ?? "",
    last: data.name?.family ?? "",
    dob: data.date_of_birth ?? "",
    expiry: data.document_expiration_date ?? "",
    address: undefined,
  };

  if (data.address) {
    const address: AddressData = {
      address: data.address.address_1,
      address2: data.address.address_2 ?? "",
      city: data.address.city,
      state: data.address.jurisdiction_code,
      ZIP: data.address.postal_code.substring(0, 5),
      country: data.country === "UnitedStates" ? "US" : "",
    };

    id.address = address;
  }

  return id;
};

const decodeMrtd = (value: string): IdData => {
  let lines = value.split("\n");
  if (lines.length === 1) {
    if (lines[0].length === 90) {
      lines = [
        lines[0].substring(0, 30),
        lines[0].substring(30, 60),
        lines[0].substring(60, 90),
      ];
    } else if (lines[0].length === 72) {
      lines = [lines[0].substring(0, 36), lines[0].substring(36, 72)];
    } else if (lines[0].length === 88) {
      lines = [lines[0].substring(0, 44), lines[0].substring(44, 88)];
    }
  }
  const data = mrtd.parse(lines.join("\n"));
  return {
    documentType: "MRTD",
    first: data.name.secondary,
    last: data.name.primary,
    dob: mrtdDate(data.birthday, false).toISOString().slice(0, 10),
    expiry: mrtdDate(data.expiry, true).toISOString().slice(0, 10),
  };
};

export const BarcodeScanner: Component<{ emitter: Emitter<BarcodeEmitter> }> = (
  props,
) => {
  const [show, setShow] = createSignal(false);

  const [pairedHidDevices, { refetch }] = createResource(async () => {
    if (!HID_SUPPORTED) {
      return [];
    }

    return filterDevices(await navigator.hid.getDevices());
  });

  const disconnect = () => {
    refetch();
    setShow(true);
  };

  createEffect(() => {
    if (pairedHidDevices.latest?.length === 0 && HID_SUPPORTED) {
      setShow(true);
    }
  });

  createEffect(() => {
    if (HID_SUPPORTED) {
      navigator.hid.addEventListener("connect", refetch);
      navigator.hid.addEventListener("disconnect", disconnect);

      onCleanup(() => {
        navigator.hid.removeEventListener("connect", refetch);
        navigator.hid.removeEventListener("disconnect", disconnect);
      });
    }
  });

  const pair = async () => {
    if (await requestHidDevice()) {
      refetch();
    }
  };

  const decodeRawScan = (value: string) => {
    if (value.startsWith("@")) {
      try {
        const id = decodeAamva(value);
        props.emitter.emit("idCard", id);
        return;
      } catch (err) {
        console.warn("data starting with @ was not aamva", err);
      }
    }

    if (value.startsWith("http")) {
      try {
        const url = new URL(value);
        props.emitter.emit("url", url);
        return;
      } catch (err) {
        console.warn("data starting with http was not url", err);
      }
    }

    try {
      const id = decodeMrtd(value);
      props.emitter.emit("idCard", id);
      return;
    } catch (err) {
      console.warn("data was not mrtd", err);
    }

    console.warn("unknown data scanned");
  };

  createEffect(() => {
    props.emitter.on("rawScan", decodeRawScan);
  });

  return (
    <div class="card mb-3">
      <div class="card-header">
        <h5 class="card-heading mb-0">
          <div class="row align-items-center g-1">
            <div class="col">
              <IconAndLabel children="Local Scanner" icon={faKeyboard} fw />
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
          when={HID_SUPPORTED}
          fallback={
            <div class="card-body pb-0">
              <div class="alert alert-warning">WebHID not supported</div>
            </div>
          }
        >
          <Suspense
            fallback={
              <div class="card-body pb-0">
                <h2>Loading devices...</h2>
              </div>
            }
          >
            <For
              each={pairedHidDevices()}
              fallback={
                <p class="card-body pb-0 mb-0">No paired devices found</p>
              }
            >
              {(device) => (
                <div class="card-body pb-0">
                  <AttachedDevice
                    device={device}
                    triggerRefresh={refetch}
                    emitRawScan={(value) => {
                      props.emitter.emit("rawScan", value);
                    }}
                  />
                </div>
              )}
            </For>

            <div class="card-body">
              <button class="btn btn-info me-1" onClick={() => pair()}>
                Connect New Device
              </button>
            </div>
          </Suspense>
        </Show>
      </div>
    </div>
  );
};
