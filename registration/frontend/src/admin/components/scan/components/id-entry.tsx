import {
  faCakeCandles,
  faCalendarXmark,
  faIdCard,
  faPlus,
} from "@fortawesome/free-solid-svg-icons";
import { createShortcut } from "@solid-primitives/keyboard";
import { differenceInYears } from "date-fns/differenceInYears";
import { type Component, Show, createMemo } from "solid-js";

import { CloseButton } from "@components/close-button";
import { IconAndLabel } from "@components/icon-and-label";

import type { IdData } from "..";
import { NameBirthday } from "./scan-pii";

export const IdEntry: Component<{ data: IdData; remove(): void }> = (props) => {
  const expirationDate = () => new Date(props.data.expiry);
  const expired = () => new Date() > expirationDate();

  const underAge = () => differenceInYears(new Date(), props.data.dob) < 18;

  const color = () => (expired() || underAge() ? "warning" : "success");

  const regUrl = createMemo(() => {
    const url = new URL("/registration/onsite", window.location.href);
    url.searchParams.set("firstName", props.data.first);
    url.searchParams.set("lastName", props.data.last);
    url.searchParams.set("dob", props.data.dob);
    if (props.data.address) {
      const address = props.data.address;
      url.searchParams.set("address1", address.address);
      if (address.address2) url.searchParams.set("address2", address.address2);
      url.searchParams.set("city", address.city);
      url.searchParams.set("state", address.state);
      url.searchParams.set("postalCode", address.ZIP.substring(0, 5));
    }
    return url.toString();
  });

  createShortcut(
    ["Control", "M"],
    () => {
      window.open(regUrl(), "register");
    },
    {
      preventDefault: true,
    },
  );

  return (
    <div class={`card border-${color()}`}>
      <div class={`card-header text-bg-${color()}`}>
        <div class="row align-items-center">
          <div class="col">
            <span class="me-1">
              <IconAndLabel
                children={`ID Card (${props.data.documentType})`}
                icon={faIdCard}
                fw
              />
            </span>

            <Show when={expired()}>
              <span class="badge text-bg-info me-1">
                <IconAndLabel children="Expired" icon={faCalendarXmark} fw />
              </span>
            </Show>

            <Show when={underAge()}>
              <span class="badge text-bg-info me-1">
                <IconAndLabel children="Under 18" icon={faCakeCandles} fw />
              </span>
            </Show>
          </div>

          <div class="col-auto">
            <CloseButton close={() => props.remove()} />
          </div>
        </div>
      </div>

      <div class="card-body">
        <div class="card-text mb-3">
          <NameBirthday
            name={`${props.data.first} ${props.data.last}`}
            birthday={props.data.dob}
          />
        </div>

        <div>
          <a
            href={regUrl()}
            class="btn btn-secondary"
            target="register"
            title="Control+M"
          >
            <IconAndLabel children="Create Attendee" icon={faPlus} fw />
          </a>
        </div>
      </div>
    </div>
  );
};
