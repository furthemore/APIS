import {
  faHospital,
  faIdBadge,
  faSignature,
  faSyringe,
  faUnlock,
} from "@fortawesome/free-solid-svg-icons";
import { type Component, For, Match, Show, Switch } from "solid-js";

import { CloseButton } from "@components/close-button";
import { IconAndLabel } from "@components/icon-and-label";

import { type ShcData, type ShcMatch } from "..";
import { NameBirthday } from "./scan-pii";

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

  const color = () => (isValid() ? "success" : "danger");

  return (
    <div class={`card border-${color()}`}>
      <div class={`card-header text-bg-${color()}`}>
        <div class="row align-items-center">
          <div class="col d-flex column-gap-2 align-items-center flex-wrap">
            <div>
              <IconAndLabel children="Vaccination Record" icon={faSyringe} fw />
            </div>

            <Show when={!props.shcMatch.dob || !props.shcMatch.name}>
              <div class="badge text-bg-info">
                <IconAndLabel icon={faIdBadge} fw>
                  <Switch>
                    <Match when={!props.shcMatch.dob && !props.shcMatch.name}>
                      Mismatched Name and Birthday
                    </Match>
                    <Match when={!props.shcMatch.name}>Mismatched Name</Match>
                    <Match when={!props.shcMatch.dob}>
                      Mismatched Birthday
                    </Match>
                  </Switch>
                </IconAndLabel>
              </div>
            </Show>

            <Show
              when={
                !props.data.verification.trusted ||
                !props.data.verification.verified
              }
            >
              <div class="badge text-bg-info">
                <IconAndLabel icon={faUnlock} fw>
                  <Switch>
                    <Match
                      when={
                        !props.data.verification.trusted &&
                        !props.data.verification.verified
                      }
                    >
                      Untrusted and Unverified
                    </Match>
                    <Match when={!props.data.verification.trusted}>
                      Untrusted
                    </Match>
                    <Match when={!props.data.verification.verified}>
                      Unverified
                    </Match>
                  </Switch>
                </IconAndLabel>
              </div>
            </Show>
          </div>

          <div class="col-auto">
            <CloseButton close={() => props.remove()} />
          </div>
        </div>
      </div>

      <div class="card-body">
        <NameBirthday
          name={props.data.name}
          birthday={props.data.birthday}
          shcMatch={props.shcMatch}
        />

        <table class="table-sm my-2 table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Vaccine</th>
              <th>Lot</th>
            </tr>
          </thead>
          <tbody>
            <For
              each={props.data.vaccines}
              fallback={
                <tr>
                  <td colSpan={3}>No records.</td>
                </tr>
              }
            >
              {(vaccine) => {
                return (
                  <tr>
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

      <div class="card-footer d-flex column-gap-2">
        <span
          class="badge"
          classList={{
            "text-bg-success": props.data.verification.trusted,
            "text-bg-danger": !props.data.verification.trusted,
          }}
          title="Issuer"
        >
          <IconAndLabel
            children={props.data.verification.issuer}
            icon={faHospital}
            fw
          />
        </span>

        <span
          class="badge"
          classList={{
            "text-bg-success": props.data.verification.verified,
            "text-bg-danger": !props.data.verification.verified,
          }}
          title="Signature Status"
        >
          <IconAndLabel
            children={
              props.data.verification.verified ? "Verified" : "Not Verified"
            }
            icon={faSignature}
            fw
          />
        </span>
      </div>
    </div>
  );
};
