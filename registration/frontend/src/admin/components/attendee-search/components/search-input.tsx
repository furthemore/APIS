import { createShortcut } from "@solid-primitives/keyboard";
import { type Component, type Setter, createEffect } from "solid-js";

export const SearchInput: Component<{
  value: string;
  attendeeCount: number;
  selectedAttendee?: number;
  setSearchFieldValue: Setter<string>;
  setSearchQuery: Setter<string>;
  setSelectedAttendee: Setter<number | undefined>;
}> = (props) => {
  let searchInputRef!: HTMLInputElement;

  createEffect(() => {
    searchInputRef.value = props.value;
  });

  createShortcut(["Alt", "F"], () => {
    props.setSearchQuery("");
    searchInputRef.focus();
  });

  const onInput = (ev: InputEvent & { target: HTMLInputElement }) => {
    props.setSearchFieldValue(ev.target.value);

    if (ev.target.value.length === 0) {
      props.setSearchQuery("");
    }
  };

  const onKeyDown = (ev: KeyboardEvent) => {
    const key = ev.key;

    if (key === "Enter") {
      ev.preventDefault();
      props.setSearchQuery(searchInputRef.value);
      return;
    }

    if (key !== "ArrowDown" && key !== "ArrowUp") return;
    ev.preventDefault();

    const currentlySelected = props.selectedAttendee || 0;
    const entryCount = props.attendeeCount;

    switch (ev.key) {
      case "ArrowDown":
        if (currentlySelected + 2 <= entryCount) {
          props.setSelectedAttendee(currentlySelected + 1);
        }
        break;
      case "ArrowUp":
        if (currentlySelected > 0) {
          props.setSelectedAttendee(currentlySelected - 1);
        }
        break;
    }
  };

  return (
    <input
      type="search"
      name="search"
      class="form-control"
      placeholder="Enter names or badge number"
      autofocus={true}
      autocomplete="off"
      ref={searchInputRef}
      onInput={onInput}
      onKeyDown={onKeyDown}
    />
  );
};
