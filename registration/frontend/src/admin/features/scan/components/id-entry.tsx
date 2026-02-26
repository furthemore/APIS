import {
  faCakeCandles,
  faCalendarXmark,
  faClipboardUser,
  faIdCard,
  faPlus,
} from "@fortawesome/free-solid-svg-icons";
import { createHotkey } from "@tanstack/solid-hotkeys";
import { differenceInYears } from "date-fns/differenceInYears";
import { type Component, Show } from "solid-js";

import { type AttendeeDetails, urlForOnsiteDetails } from "@admin/api";
import { DisplayRegistrationButton } from "@admin/features/display-registration";
import { CloseButton } from "@components/close-button";
import { IconAndLabel } from "@components/icon-and-label";

import type { IdData } from "..";
import { NameBirthday } from "./scan-pii";

export const IdEntry: Component<{ data: IdData; remove(): void }> = (props) => {
  const expirationDate = () => new Date(props.data.expiry);
  const expired = () => new Date() > expirationDate();

  const underAge = () => differenceInYears(new Date(), props.data.dob) < 18;

  const color = () => (expired() || underAge() ? "warning" : "success");

  const attendeeDetails = () => {
    const details: AttendeeDetails = {
      firstName: props.data.first,
      lastName: props.data.last,
      dob: props.data.dob,
    };

    if (props.data.address) {
      const address = props.data.address;
      details.address1 = address.address;
      if (address.address2) details.address2 = address.address2;
      details.city = address.city;
      details.state = address.state;
      details.postalCode = address.ZIP.substring(0, 5);
    }

    return details;
  };

  const regUrl = () => urlForOnsiteDetails(attendeeDetails()).toString();

  createHotkey("Mod+M", () => {
    globalThis.open(regUrl(), "register");
  });

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
          <DisplayRegistrationButton
            details={attendeeDetails}
            class="btn btn-secondary me-1"
          >
            <IconAndLabel
              children="Prompt Registration"
              icon={faClipboardUser}
            />
          </DisplayRegistrationButton>

          <a
            href={regUrl()}
            class="btn btn-info"
            target="register"
            title="Control+M"
          >
            <IconAndLabel children="New Attendee" icon={faPlus} fw />
          </a>
        </div>
      </div>
    </div>
  );
};
