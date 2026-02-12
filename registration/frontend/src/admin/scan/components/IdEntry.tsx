import { createShortcut } from "@solid-primitives/keyboard";
import { differenceInYears } from "date-fns/differenceInYears";
import { type Component, Show } from "solid-js";

import { type IdData } from "..";
import { CartManager } from "../../cart";
import {
  type AttendeeDetails,
  DisplayRegistrationButton,
} from "../../components/DisplayRegistration";
import { CloseButton } from "./CloseButton";
import { NameBirthday } from "./ScanPii";

export const IdEntry: Component<{
  data: IdData;
  remove(): void;
  cartManager: CartManager;
}> = (props) => {
  const expirationDate = () => new Date(props.data.expiry);
  const expired = () => new Date() > expirationDate();

  const underAge = () => differenceInYears(new Date(), props.data.dob) < 18;

  const panelClasses = () => {
    return {
      "is-warning": expired() || underAge(),
      "is-success": !expired() && !underAge(),
    };
  };

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

  const regUrl = () =>
    props.cartManager.getOnsiteUrl(attendeeDetails()).toString();

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
    <article class="message control" classList={panelClasses()}>
      <div class="message-header">
        <span class="icon-text mr-3">
          <span class="icon">
            <i class="fa-solid fa-id-card"></i>
          </span>
          <span>{`ID Card (${props.data.documentType})`}</span>
        </span>

        <div class="is-flex-grow-1">
          <div class="tags">
            <Show when={expired()}>
              <span class="tag">
                <span class="icon">
                  <i class="fa-solid fa-calendar-xmark"></i>
                </span>
                <span>Expired</span>
              </span>
            </Show>

            <Show when={underAge()}>
              <span class="tag">
                <span class="icon">
                  <i class="fa-solid fa-cake-candles"></i>
                </span>
                <span>Under 18</span>
              </span>
            </Show>
          </div>
        </div>

        <CloseButton close={() => props.remove()} />
      </div>

      <div class="message-body">
        <NameBirthday
          name={`${props.data.first} ${props.data.last}`}
          birthday={props.data.dob}
        />

        <div class="buttons">
          <a
            href={regUrl()}
            class="button is-link"
            target="register"
            title="Control+M"
          >
            <span class="icon">
              <i class="fas fa-plus"></i>
            </span>
            <span>Create Attendee</span>
          </a>

          <DisplayRegistrationButton
            details={attendeeDetails}
            cartManager={props.cartManager}
            class="button is-secondary"
          >
            <span class="icon">
              <i class="fas fa-clipboard-user"></i>
            </span>
            <span>Prompt Registration</span>
          </DisplayRegistrationButton>
        </div>
      </div>
    </article>
  );
};
