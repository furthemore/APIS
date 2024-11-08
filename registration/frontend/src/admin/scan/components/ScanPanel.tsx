import { Component, createEffect, createMemo, Show } from "solid-js";
import { createStore } from "solid-js/store";

import { IdEntry } from "./IdEntry";
import { ShcEntry } from "./ShcEntry";
import { UrlEntry } from "./UrlEntry";
import { IdData, ShcData } from "..";
import { MqttEmitter } from "../../mqtt";

type ScanStore = {
  id?: IdData;
  shc?: ShcData;
  url?: string;
};

export const ScanPanel: Component<{
  gotScannedName(name: string): void;
  emitter: MqttEmitter;
}> = (props) => {
  const [store, setStore] = createStore<ScanStore>({
    id: null,
    shc: null,
    url: null,
  });

  const shcMatch = createMemo(() => {
    if (!store.id || !store.shc) return { name: true, dob: true };

    const idName = `${store.id.first} ${store.id.last}`;
    const name = idName.localeCompare(store.shc.name) === 0;

    const dob = store.id.dob === store.shc.birthday;

    return { name, dob };
  });

  const hasAnyScans = () => store.id || store.shc || store.url;

  createEffect(() => {
    const id = store.id;
    if (id) {
      props.gotScannedName(`${id.first} ${id.last}`);
    }
  });

  createEffect(() => {
    const emitter = props.emitter;

    emitter.on("open", (payload) => {
      const url = payload?.["url"];
      if (url) {
        window.open(url, "link");
        setStore("url", url);
      } else {
        console.error("Open command missing URL");
      }
    });

    emitter.on("scan/id", (payload: IdData) => {
      if (payload) {
        setStore("id", payload);
      } else {
        console.error("Missing ID scan payload");
      }
    });

    emitter.on("scan/shc", (payload: ShcData) => {
      if (payload) {
        setStore("shc", payload);
      } else {
        console.error("Missing SHC scan payload");
      }
    });
  });

  return (
    <div class="block">
      <div class="panel is-info">
        <div class="panel-heading">
          <div class="columns">
            <div class="column">Scanner Entries</div>

            <div class="column is-narrow">
              <button
                class="button is-warning is-small is-light"
                disabled={!hasAnyScans()}
                onClick={() => setStore({ id: null, shc: null, url: null })}
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        <Show when={!hasAnyScans()}>
          <div class="panel-block">No items scanned.</div>
        </Show>

        <Show when={store.id}>
          <div class="panel-block">
            <IdEntry data={store.id} remove={() => setStore("id", null)} />
          </div>
        </Show>

        <Show when={store.shc}>
          <div class="panel-block">
            <ShcEntry
              data={store.shc}
              shcMatch={shcMatch()}
              remove={() => setStore("shc", null)}
            />
          </div>
        </Show>

        <Show when={store.url}>
          <div class="panel-block">
            <UrlEntry url={store.url} remove={() => setStore("url", null)} />
          </div>
        </Show>
      </div>
    </div>
  );
};
