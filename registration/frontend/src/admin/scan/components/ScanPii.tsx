import { Component } from "solid-js";
import { differenceInYears } from "date-fns/differenceInYears";

import { MismatchedData } from "./MismatchedData";
import { ShcMatch } from "..";

export const NameBirthday: Component<{
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
