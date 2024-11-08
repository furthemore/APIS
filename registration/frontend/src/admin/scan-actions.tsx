import {
  Component,
  createEffect,
  createMemo,
  createSignal,
  For,
  JSX,
  Show,
  useContext,
} from "solid-js";

import emitter from "./mqtt";
import { differenceInYears } from "date-fns";
import { ConfigContext } from "./providers/config-provider";

interface IdData {
  first: string;
  last: string;
  dob: string;
  expiry: string;
  address: string;
  address2: string;
  city: string;
  state: string;
  ZIP: string;
  country: string;
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

const [scanLog, setScanLog] = createSignal<ScanLog>({
  url: undefined,
  id: undefined,
  shc: undefined,
});

export const ScanPanel: Component<{
  gotScannedName(name: string): void;
}> = (props) => {
  const shcMatch = createMemo(() => {
    const data = scanLog();
    if (!data.id || !data.shc) return { name: true, dob: true };

    const idName = `${data.id.first} ${data.id.last}`;
    const name = idName.localeCompare(data.shc.name) === 0;

    const dob = data.id.dob === data.shc.birthday;

    return { name, dob };
  });

  createEffect(() => {
    const name = scanLog().id?.last;
    if (name) {
      props.gotScannedName(name);
    }
  });

  const hasAnyScans = () => scanLog().id || scanLog().shc || scanLog().url;

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
                onClick={() =>
                  setScanLog({ url: undefined, id: undefined, shc: undefined })
                }
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        <Show when={!hasAnyScans()}>
          <div class="panel-block">No items scanned.</div>
        </Show>

        <Show when={scanLog().id}>
          <div class="panel-block">
            <IdEntry data={scanLog().id} />
          </div>
        </Show>

        <Show when={scanLog().shc}>
          <div class="panel-block">
            <ShcEntry data={scanLog().shc} shcMatch={shcMatch()} />
          </div>
        </Show>

        <Show when={scanLog().url}>
          <div class="panel-block">
            <UrlEntry url={scanLog().url} />
          </div>
        </Show>
      </div>
    </div>
  );
};

const CloseButton: Component<{ close(): any }> = (props) => {
  return (
    <button class="delete" aria-label="delete" onClick={props.close}></button>
  );
};

const MismatchedData: Component<{
  matched: boolean;
  message: string;
  children: JSX.Element;
}> = (props) => {
  return (
    <Show when={!props.matched} fallback={props.children}>
      <span class="icon-text has-text-warning" title={props.message}>
        <span class="icon">
          <i class="fa-solid fa-triangle-exclamation"></i>
        </span>
        {props.children}
      </span>
    </Show>
  );
};

const NameBirthday: Component<{
  name: string;
  birthday: string;
  shcMatch?: ShcMatch;
}> = (props) => {
  const age = () => {
    return differenceInYears(new Date(), props.birthday);
  };

  return (
    <div class="columns">
      <div class="column">
        <MismatchedData
          matched={!props.shcMatch || props.shcMatch?.name}
          message="Name does not match ID"
        >
          <span class="has-text-weight-semibold">{props.name}</span>
        </MismatchedData>
      </div>
      <div class="column has-text-right-desktop has-text-left-tablet">
        <MismatchedData
          matched={!props.shcMatch || props.shcMatch?.dob}
          message="Birthday does not match ID"
        >
          <span class="icon-text">
            <span class="icon">
              <i class="fas fa-cake-candles"></i>
            </span>
            <span>{`${props.birthday} (${age()} years)`}</span>
          </span>
        </MismatchedData>
      </div>
    </div>
  );
};

const UrlEntry: Component<{ url: string }> = (props) => {
  return (
    <article class="message is-link control">
      <div class="message-header">
        Link
        <CloseButton
          close={() => setScanLog({ ...scanLog(), url: undefined })}
        />
      </div>

      <div class="message-body">
        <a href={props.url} target="link">
          {props.url}
        </a>
      </div>
    </article>
  );
};

const IdEntry: Component<{ data: IdData }> = (props) => {
  const config = useContext(ConfigContext);

  const expirationDate = () => new Date(props.data.expiry);
  const expired = () => new Date() > expirationDate();

  const panelClasses = () => {
    return {
      "is-warning": expired(),
      "is-success": !expired(),
    };
  };

  const regUrl = createMemo(() => {
    let url = new URL(config.urls.onsite, window.location.href);
    url.searchParams.set("firstName", props.data.first);
    url.searchParams.set("lastName", props.data.last);
    url.searchParams.set("dob", props.data.dob);
    url.searchParams.set("address1", props.data.address);
    if (props.data.address2)
      url.searchParams.set("address2", props.data.address2);
    url.searchParams.set("city", props.data.city);
    url.searchParams.set("state", props.data.state);
    url.searchParams.set("postalCode", props.data.ZIP.substring(0, 5));
    return url.toString();
  });

  return (
    <article class="message control" classList={panelClasses()}>
      <div class="message-header">
        <span class="icon-text">
          <span class="icon">
            <i class="fa-solid fa-id-card"></i>
          </span>
          <span>ID Card</span>
        </span>

        <Show when={expired()}>
          <span class="ml-2">
            <i class="fa-solid fa-calendar-xmark"></i>
            {`Expired ${props.data.expiry}`}
          </span>
        </Show>

        <CloseButton
          close={() => setScanLog({ ...scanLog(), id: undefined })}
        />
      </div>

      <div class="message-body">
        <NameBirthday
          name={`${props.data.first} ${props.data.last}`}
          birthday={props.data.dob}
        />

        <div>
          <a href={regUrl()} class="button is-link" target="register">
            <span class="icon">
              <i class="fas fa-plus"></i>
            </span>
            <span>Create Attendee</span>
          </a>
        </div>
      </div>
    </article>
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
    <article
      class="message control"
      classList={{
        "is-success": props.data.verification.trusted,
        "is-warning": !props.shcMatch.dob || !props.shcMatch.name,
        "is-danger": !props.data.verification.verified,
      }}
    >
      <div class="message-header">
        <span class="icon-text">
          <span class="icon">
            <i class="fa-solid fa-syringe"></i>
          </span>
          <span>Vaccination Record - {status()}</span>
        </span>

        <CloseButton
          close={() => setScanLog({ ...scanLog(), shc: undefined })}
        />
      </div>
      <div class="message-body">
        <NameBirthday
          name={props.data.name}
          birthday={props.data.birthday}
          shcMatch={props.shcMatch}
        />

        <table class="table is-narrow is-fullwidth">
          <thead>
            <tr>
              <th class="has-text-nowrap">Date</th>
              <th>Vaccine</th>
              <th class="has-text-nowrap">Lot</th>
            </tr>
          </thead>
          <tbody>
            <For each={props.data.vaccines}>
              {(vaccine, index) => {
                return (
                  <tr data-index={index()}>
                    <td class="has-text-nowrap">{vaccine.date}</td>
                    <td>{vaccine.name}</td>
                    <td class="has-text-nowrap">{vaccine.lotNumber}</td>
                  </tr>
                );
              }}
            </For>
          </tbody>
        </table>
      </div>
    </article>
  );
};

emitter.on("open", (payload) => {
  const url = payload?.["url"];
  if (!url) {
    console.error("Open command missing URL");
    return;
  }

  window.open(url, "link");
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
