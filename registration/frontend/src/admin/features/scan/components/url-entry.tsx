import { faLink } from "@fortawesome/free-solid-svg-icons";
import { type Component } from "solid-js";

import { CloseButton } from "@components/close-button";
import { IconAndLabel } from "@components/icon-and-label";

export const UrlEntry: Component<{ url: string; remove(): void }> = (props) => {
  return (
    <div class="card border-info">
      <div class="card-header text-bg-info">
        <div class="row align-items-center">
          <div class="col">
            <IconAndLabel children="Link" icon={faLink} fw />
          </div>

          <div class="col-auto">
            <CloseButton close={() => props.remove()} />
          </div>
        </div>
      </div>

      <div class="card-body">
        <a href={props.url} target="link" class="card-link">
          {props.url}
        </a>
      </div>
    </div>
  );
};
