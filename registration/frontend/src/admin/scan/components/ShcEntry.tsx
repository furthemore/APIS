import { Component, For, Match, Show, Switch } from "solid-js";

import { ShcData, ShcMatch } from "..";
import { CloseButton } from "./CloseButton";
import { NameBirthday } from "./ScanPii";

export const ShcEntry: Component<{
  data: ShcData;
  shcMatch: ShcMatch;
  remove(): void;
}> = (props) => {
  const isValid = () =>
    props.data.verification.trusted &&
    props.data.verification.verified &&
    props.shcMatch.dob &&
    props.shcMatch.name;

  return (
    <article
      class="message control"
      classList={{
        "is-success": isValid(),
        "is-danger": !isValid(),
      }}
    >
      <div class="message-header">
        <span class="icon-text mr-3">
          <span class="icon">
            <i class="fa-solid fa-syringe"></i>
          </span>
          <span>Vaccination Record</span>
        </span>

        <Show when={!isValid()}>
          <div class="is-flex-grow-1">
            <div class="tags">
              <Show when={!props.shcMatch.dob || !props.shcMatch.name}>
                <div class="tag is-warning">
                  <div class="icon">
                    <i class="fas fa-id-badge"></i>
                  </div>
                  <Switch>
                    <Match when={!props.shcMatch.dob && !props.shcMatch.name}>
                      <span>Mismatched Name and Birthday</span>
                    </Match>
                    <Match when={!props.shcMatch.name}>
                      <span>Mismatched Name</span>
                    </Match>
                    <Match when={!props.shcMatch.dob}>
                      <span>Mismatched Birthday</span>
                    </Match>
                  </Switch>
                </div>
              </Show>
              <Show
                when={
                  !props.data.verification.trusted ||
                  !props.data.verification.verified
                }
              >
                <div class="tag is-warning">
                  <span class="icon">
                    <i class="fas fa-unlock"></i>
                  </span>
                  <Switch>
                    <Match
                      when={
                        !props.data.verification.trusted &&
                        !props.data.verification.verified
                      }
                    >
                      <span>Untrusted and Unverified</span>
                    </Match>
                    <Match when={!props.data.verification.trusted}>
                      <span>Untrusted</span>
                    </Match>
                    <Match when={!props.data.verification.verified}>
                      <span>Unverified</span>
                    </Match>
                  </Switch>
                </div>
              </Show>
            </div>
          </div>
        </Show>

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

        <div class="field is-grouped is-grouped-multiline">
          <div class="control">
            <div class="tags has-addons">
              <span class="tag is-dark">Issuer</span>
              <span
                class="tag"
                classList={{
                  "is-success": props.data.verification.trusted,
                  "is-danger": !props.data.verification.trusted,
                }}
              >
                {props.data.verification.issuer}
              </span>
            </div>
          </div>

          <div class="control">
            <div class="tags has-addons">
              <span class="tag is-dark">Signature</span>
              <span
                class="tag"
                classList={{
                  "is-success": props.data.verification.verified,
                  "is-danger": !props.data.verification.verified,
                }}
              >
                {props.data.verification.verified ? "Verified" : "Not Verified"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
};
