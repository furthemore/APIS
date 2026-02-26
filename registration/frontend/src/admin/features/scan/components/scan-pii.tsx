import { faCakeCandles } from "@fortawesome/free-solid-svg-icons";
import { differenceInYears } from "date-fns/differenceInYears";
import { type Component } from "solid-js";

import { IconAndLabel } from "@components/icon-and-label";

import type { ShcMatch } from "..";
import { MismatchedData } from "./mismatched-data";

export const NameBirthday: Component<{
  name: string;
  birthday: string;
  shcMatch?: ShcMatch;
}> = (props) => {
  const age = () => {
    return differenceInYears(new Date(), props.birthday);
  };

  return (
    <div class="row align-items-center">
      <div class="col-md">
        <MismatchedData
          matched={!props.shcMatch || props.shcMatch?.name}
          message="Name does not match ID"
        >
          <span class="fw-semibold">{props.name}</span>
        </MismatchedData>
      </div>
      <div class="col-md-auto text-md-end">
        <MismatchedData
          matched={!props.shcMatch || props.shcMatch?.dob}
          message="Birthday does not match ID"
        >
          <IconAndLabel
            children={`${props.birthday} (${age()} years)`}
            icon={faCakeCandles}
            fw
          />
        </MismatchedData>
      </div>
    </div>
  );
};
