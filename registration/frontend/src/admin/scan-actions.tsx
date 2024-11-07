import { Component, createSignal, For, Show } from "solid-js";
import emitter from "./mqtt";
import { render } from "solid-js/web";

interface IdData {
  expirationDate: string;
  dateOfBirth: string;
  age: number;
  givenName: string;
  familyName: string;
}

interface ShcData {
  name: string;
  birthday: string;
  verification: ShcIssuer;
  vaccines: ShcVaccine[];
}

interface ShcIssuer {
  issuer: string;
  verified: boolean;
  trusted: boolean;
}

interface ShcVaccine {
  name: string;
  lotNumber: string;
  status: string;
  date: string;
  performer: string;
}

interface ScanLog {
  url: string | undefined;
  id: IdData | undefined;
  shc: ShcData | undefined;
}

interface ShcMatch {
  name: boolean;
  dob: boolean;
}

const scanPanel = document.getElementById("scan-panel");
const [scanLog, setScanLog] = createSignal<ScanLog>({
  url: undefined,
  id: undefined,
  shc: undefined,
});

function ScanPanel() {
  const shcMatch = () => {
    const data = scanLog();
    if (!data.id || !data.shc) return { name: false, dob: false };

    const idName = `${data.id.givenName} ${data.id.familyName}`;
    const name = idName.localeCompare(data.shc.name) === 0;

    const dob = data.id.dateOfBirth === data.shc.birthday;

    return { name, dob };
  };

  return (
    <>
      <div class="panel-heading">
        Scanner History
        <button
          class="btn btn-xs btn-primary right"
          onClick={() =>
            setScanLog({ url: undefined, id: undefined, shc: undefined })
          }
        >
          Clear
        </button>
      </div>

      <div>
        <Show when={scanLog().id}>
          <IdEntry data={scanLog().id} />
        </Show>

        <Show when={scanLog().shc}>
          <ShcEntry data={scanLog().shc} shcMatch={shcMatch()} />
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
        <a href={props.url} target="_blank">
          {props.url}
        </a>
        <CloseButton
          close={() => setScanLog({ ...scanLog(), url: undefined })}
        />
      </div>
    </div>
  );
};

const IdEntry: Component<{ data: IdData }> = (props) => {
  const expirationDate = new Date(props.data.expirationDate);
  const expired = new Date() > expirationDate;

  const panelClasses = {
    "panel-warning": expired,
    "panel-primary": !expired,
  };

  return (
    <div class="panel" classList={panelClasses}>
      <div class="panel-heading">
        <i class="fa-solid fa-id-card"></i>
        <span>License Scanned</span>
        <Show when={expired}>
          <span>
            <i class="fa-solid fa-calendar-xmark"></i>
            {` Expired ${props.data.expirationDate}`}
          </span>
        </Show>
        <CloseButton
          close={() => setScanLog({ ...scanLog(), id: undefined })}
        />
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

const ShcEntry: Component<{ data: ShcData; shcMatch: ShcMatch }> = (props) => {
  const status = () => {
    let status = "Partially Verified";
    if (props.data.verification.trusted) {
      status = "Verified";
    } else if (!props.data.verification.verified) {
      status = "Not Verified";
    }
    return status;
  };

  return (
    <div
      class="panel"
      classList={{
        success: props.data.verification.trusted,
        danger: !props.data.verification.verified,
      }}
    >
      <div class="panel-heading">
        <i class="fa-solid fa-syringe"></i> Vaccination Record - {status()}
        <CloseButton
          close={() => setScanLog({ ...scanLog(), shc: undefined })}
        />
      </div>
      <div class="panel-body">
        <Show
          when={!props.shcMatch.name}
          fallback={<strong>{props.data.name}</strong>}
        >
          <span class="text-warning" title="Name does not match ID">
            <i class="fa-solid fa-triangle-exclamation"></i>
            <strong>{props.data.name}</strong>
          </span>
        </Show>

        <table class="table table-condensed">
          <thead>
            <tr>
              <th>Date</th>
              <th>Vaccine</th>
              <th>Lot</th>
            </tr>
          </thead>
          <tbody>
            <For each={props.data.vaccines}>
              {(vaccine, index) => {
                return (
                  <tr data-index={index()}>
                    <td>{vaccine.date}</td>
                    <td>{vaccine.name}</td>
                    <td>{vaccine.lotNumber}</td>
                  </tr>
                );
              }}
            </For>
          </tbody>
        </table>
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

emitter.on("scan/shc", (payload: ShcData) => {
  if (!payload) {
    console.error("Missing SHC scan payload");
    return;
  }

  setScanLog({
    ...scanLog(),
    shc: payload,
  });
});

render(ScanPanel, scanPanel);
