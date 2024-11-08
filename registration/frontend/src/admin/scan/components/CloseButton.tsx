import { Component } from "solid-js";

export const CloseButton: Component<{ close(): any }> = (props) => {
  return (
    <button class="delete" aria-label="delete" onClick={props.close}></button>
  );
};
