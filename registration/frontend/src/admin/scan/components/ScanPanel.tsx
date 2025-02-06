import { Component, createEffect, createMemo, Show } from "solid-js";
import { createShortcut } from "@solid-primitives/keyboard";
import { createStore } from "solid-js/store";

import { IdData, ShcData } from "..";
import { IdEntry } from "./IdEntry";
import { MqttEmitter } from "../../mqtt";
import { ShcEntry } from "./ShcEntry";
import { UrlEntry } from "./UrlEntry";

type ScanStore = {
  id?: IdData;
  shc?: ShcData;
  url?: string;
};

export const ScanPanel: Component<{
  gotScannedName(name: string, birthday?: string): void;
  emitter: MqttEmitter;
}> = (props) => {
  const [store, setStore] = createStore<ScanStore>({
    id: undefined,
    shc: undefined,
    url: undefined,
  });

  const clear = () => {
    setStore({ id: undefined, shc: undefined, url: undefined });
  };

  let panel!: HTMLDivElement;

  createShortcut(["Alt", "S"], clear.bind(this));

  createShortcut(["Alt", "D"], () => {
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

  createEffect(() => {
    const emitter = props.emitter;

    emitter.on("open", (payload: object | null) => {
      if (payload && "url" in payload) {
        const url = payload["url"] as string;
        setStore("url", url);
      } else {
        console.error("Open command missing URL");
      }
    });

    emitter.on("scan/id", (payload: object | null) => {
      if (payload) {
        setStore("id", payload);
      } else {
        console.error("Missing ID scan payload");
      }
    });

    emitter.on("scan/shc", (payload: object | null) => {
      if (payload) {
        setStore("shc", payload);
      } else {
        console.error("Missing SHC scan payload");
      }
    });
  });

  return (
    <div class="block" ref={panel}>
      <div class="panel is-dark">
        <div class="panel-heading">
          <div class="columns is-mobile">
            <div class="column is-align-self-center">Scanner Entries</div>

            <div class="column is-narrow">
              <button
                class="button is-warning is-small"
                disabled={!hasAnyScans()}
                title="Alt+S"
                onClick={() => clear()}
              >
                <span class="icon">
                  <i class="fas fa-xmark"></i>
                </span>
                <span>Clear</span>
              </button>
            </div>
          </div>
        </div>

        <Show when={!hasAnyScans()}>
          <div class="panel-block">No items scanned.</div>
        </Show>

        <Show when={store.id}>
          <div class="panel-block">
            <IdEntry
              data={store.id!}
              remove={() => setStore("id", undefined)}
            />
          </div>
        </Show>

        <Show when={store.shc}>
          <div class="panel-block">
            <ShcEntry
              data={store.shc!}
              shcMatch={shcMatch()}
              remove={() => setStore("shc", undefined)}
            />
          </div>
        </Show>

        <Show when={store.url}>
          <div class="panel-block">
            <UrlEntry
              url={store.url!}
              remove={() => setStore("url", undefined)}
            />
          </div>
        </Show>
      </div>
    </div>
  );
};
