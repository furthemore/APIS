import { Component } from "solid-js";

import { CloseButton } from "./CloseButton";

export const UrlEntry: Component<{ url: string; remove(): void }> = (props) => {
  return (
    <article class="message is-link control">
      <div class="message-header">
        Link
        <CloseButton close={() => props.remove()} />
      </div>

      <div class="message-body">
        <a href={props.url} target="link">
          {props.url}
        </a>
      </div>
    </article>
  );
};
