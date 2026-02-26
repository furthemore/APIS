import { faBarcode, faXmark } from "@fortawesome/free-solid-svg-icons";
import { createHotkey } from "@tanstack/solid-hotkeys";
import {
  type Component,
  Show,
  createEffect,
  createMemo,
  onCleanup,
  useContext,
} from "solid-js";
import { createStore } from "solid-js/store";

import { MqttContext } from "@admin/providers/mqtt-provider";
import { IconAndLabel } from "@components/icon-and-label";

import type { IdData, ShcData } from "..";
import { IdEntry } from "./id-entry";
import { ShcEntry } from "./shc-entry";
import { UrlEntry } from "./url-entry";

type ScanStore = {
  id?: IdData;
  shc?: ShcData;
  url?: string;
};

export const Scan: Component<{
  gotScannedName(name: string, birthday?: string): void;
  readyForNext: boolean;
}> = (props) => {
  const mqtt = useContext(MqttContext)!;

  const [store, setStore] = createStore<ScanStore>({
    id: undefined,
    shc: undefined,
    url: undefined,
  });

  const clear = () => {
    setStore({ id: undefined, shc: undefined, url: undefined });
  };

  createEffect(() => {
    if (props.readyForNext) {
      clear();
    }
  });

  let panel!: HTMLDivElement;

  createHotkey("Alt+S", clear);

  createHotkey("Alt+D", () => {
    panel.scrollIntoView(false);
  });

  const shcMatch = createMemo(() => {
    if (!store.id || !store.shc) return { name: true, dob: true };

    const idName = `${store.id.first} ${store.id.last}`;
    const name =
      idName.localeCompare(store.shc.name, undefined, {
        sensitivity: "base",
      }) === 0;

    const dob = store.id.dob === store.shc.birthday;

    return { name, dob };
  });

  const hasAnyScans = () => store.id || store.shc || store.url;

  createEffect(() => {
    const id = store.id;
    if (id) {
      props.gotScannedName(`${id.first} ${id.last}`, id.dob);
    }
  });

  const setUrl = (payload: object | null) => {
    if (payload && "url" in payload) {
      const url = payload["url"] as string;
      setStore("url", url);
    } else {
      console.error("Open command missing URL");
    }
  };

  const setId = (payload: object | null) => {
    if (payload) {
      setStore("id", payload);
    } else {
      console.error("Missing ID scan payload");
    }
  };

  const setShc = (payload: object | null) => {
    if (payload) {
      setStore("shc", payload);
    } else {
      console.error("Missing SHC scan payload");
    }
  };

  createEffect(() => {
    const m = mqtt();

    m?.emitter.on("notify/scan/url", setUrl);
    m?.emitter.on("notify/scan/id", setId);
    m?.emitter.on("notify/scan/shc", setShc);

    onCleanup(() => {
      m?.emitter.off("notify/scan/url", setUrl);
      m?.emitter.off("notify/scan/id", setId);
      m?.emitter.off("notify/scan/shc", setShc);
    });
  });

  return (
    <div class="card mb-3 pb-3" ref={panel}>
      <div class="card-header">
        <div class="row align-items-center">
          <div class="col">
            <h5 class="card-title mb-0">
              <IconAndLabel children="Scans" icon={faBarcode} fw />
            </h5>
          </div>

          <div class="col-auto">
            <button
              class="btn btn-sm btn-warning"
              disabled={!hasAnyScans()}
              title="Alt+S"
              onClick={clear}
            >
              <IconAndLabel children="Clear" icon={faXmark} />
            </button>
          </div>
        </div>
      </div>

      <Show when={!hasAnyScans()}>
        <div class="card-body pb-0">No items scanned.</div>
      </Show>

      <Show when={store.id}>
        <div class="card-body pb-0">
          <IdEntry data={store.id!} remove={() => setStore("id", undefined)} />
        </div>
      </Show>

      <Show when={store.shc}>
        <div class="card-body pb-0">
          <ShcEntry
            data={store.shc!}
            shcMatch={shcMatch()}
            remove={() => setStore("shc", undefined)}
          />
        </div>
      </Show>

      <Show when={store.url}>
        <div class="card-body">
          <UrlEntry
            url={store.url!}
            remove={() => setStore("url", undefined)}
          />
        </div>
      </Show>
    </div>
  );
};
