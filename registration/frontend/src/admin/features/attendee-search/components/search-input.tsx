import { createHotkey } from "@tanstack/solid-hotkeys";
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

  createHotkey("Alt+F", () => {
    props.setSearchQuery("");
    searchInputRef.focus();
  });

  const onInput = (ev: InputEvent & { target: HTMLInputElement }) => {
    props.setSearchFieldValue(ev.target.value);

    if (ev.target.value.length === 0) {
      props.setSearchQuery("");
    }
  };

  createHotkey(
    "Enter",
    () => {
      props.setSearchQuery(searchInputRef.value);
    },
    () => ({
      target: searchInputRef,
    }),
  );

  createHotkey(
    "ArrowUp",
    () => {
      const currentlySelected = props.selectedAttendee || 0;

      if (currentlySelected > 0) {
        props.setSelectedAttendee(currentlySelected - 1);
      }
    },
    () => ({
      target: searchInputRef,
    }),
  );

  createHotkey(
    "ArrowDown",
    () => {
      const currentlySelected = props.selectedAttendee || 0;

      if (currentlySelected + 2 <= props.attendeeCount) {
        props.setSelectedAttendee(currentlySelected + 1);
      }
    },
    () => ({
      target: searchInputRef,
    }),
  );

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
    />
  );
};
