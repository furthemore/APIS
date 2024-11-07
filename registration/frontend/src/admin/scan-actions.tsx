import { Component, createSignal, Show } from "solid-js";
import emitter from "./mqtt";
import { render } from "solid-js/web";

interface IdData {
  expirationDate: string;
  dateOfBirth: string;
  age: number;
  givenName: string;
  familyName: string;
}

interface ScanLog {
  url: string | undefined;
  id: IdData | undefined;
}

const scanPanel = document.getElementById("scan-panel");
const [scanLog, setScanLog] = createSignal<ScanLog>(
  { url: undefined, id: undefined },
  { equals: false }
);

function ScanPanel() {
  return (
    <>
      <div class="panel-heading">
        Scanner History
        <button class="btn btn-xs btn-primary right" onClick={
          () => setScanLog({ url: undefined, id: undefined })
        }>Clear</button>
      </div>

      <div>
        <Show when={scanLog().id}>
          <IdEntry data={scanLog().id} />
        </Show>

        <Show when={scanLog().url}>
          <UrlEntry url={scanLog().url} />
        </Show>
      </div>
    </>
  );
}

const CloseButton: Component<{ close(): any }> = (props) => {
  return (
    <button type="button" class="close close-panel" onClick={props.close}>
      <span>&times;</span>
    </button>
  );
};

const UrlEntry: Component<{ url: string }> = (props) => {
  return (
    <div class="panel panel-default">
      <div class="panel-heading">
        <a href={props.url} target="_blank">{props.url}</a>
        <CloseButton close={
          () => setScanLog({ ...scanLog(), url: undefined })
        } />
      </div>
    </div>
  );
};

const IdEntry: Component<{ data: IdData }> = (props) => {
  const expirationDate = new Date(props.data.expirationDate);
  const expired = new Date() > expirationDate;

  const panelClasses = {
    "panel": true,
    "panel-warning": expired,
    "panel-primary": !expired
  };

  return (
    <div classList={panelClasses}>
      <div class="panel-heading">
        <i class="fa-solid fa-id-card"></i>
        <span>License Scanned</span>
        <Show when={expired}>
          <span>
            <i class="fa-solid fa-calendar-xmark"></i>
            {` Expired ${props.data.expirationDate}`}
          </span>
        </Show>
        <CloseButton close={
          () => setScanLog({ ...scanLog(), id: undefined })
        } />
      </div>
      <div class="panel-body">
        <strong>{`${props.data.givenName} ${props.data.familyName}`}</strong>
        <span class="right">
          <i class="fas fa-cake-candles"></i>
          {` ${props.data.dateOfBirth} (${props.data.age} years)`}
        </span>
      </div>
    </div>
  );
};

emitter.on("open", (payload) => {
  const url = payload?.["url"];
  if (!url) {
    console.error("Open command missing URL");
    return;
  }

  window.open(url, "_blank");
  setScanLog({
    ...scanLog(),
    url,
  });
});

emitter.on("scan/id", (payload: IdData) => {
  if (!payload) {
    console.error("Missing ID scan payload");
    return;
  }

  setScanLog({
    ...scanLog(),
    id: payload,
  });
});

render(ScanPanel, scanPanel);
