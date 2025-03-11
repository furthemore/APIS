import { createShortcut } from "@solid-primitives/keyboard";
import { differenceInYears } from "date-fns/differenceInYears";
import { Component, createMemo, Show, useContext } from "solid-js";

import { IdData } from "..";
import { ConfigContext } from "../../providers/config-provider";
import { CloseButton } from "./CloseButton";
import { NameBirthday } from "./ScanPii";

export const IdEntry: Component<{ data: IdData; remove(): void }> = (props) => {
  const config = useContext(ConfigContext)!;

  const expirationDate = () => new Date(props.data.expiry);
  const expired = () => new Date() > expirationDate();

  const underAge = () => differenceInYears(new Date(), props.data.dob) < 18;

  const panelClasses = () => {
    return {
      "is-warning": expired() || underAge(),
      "is-success": !expired() && !underAge(),
    };
  };

  const regUrl = createMemo(() => {
    let url = new URL(config.urls.onsite, window.location.href);
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
    }
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

        <div>
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
        </div>
      </div>
    </article>
  );
};
