import { Component, For } from "solid-js";

import { CloseButton } from "./CloseButton";
import { NameBirthday } from "./ScanPii";
import { ShcData, ShcMatch } from "..";

export const ShcEntry: Component<{
  data: ShcData;
  shcMatch: ShcMatch;
  remove(): void;
}> = (props) => {
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

        <CloseButton close={() => props.remove()} />
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
