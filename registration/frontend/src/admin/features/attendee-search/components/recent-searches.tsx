import { faClockRotateLeft } from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
import Fa from "solid-fa";
import { type Component, For, type Setter } from "solid-js";

export const RecentSearches: Component<{
  searches: string[];
  setSearchQuery: Setter<string>;
}> = (props) => {
  return (
    <DropdownMenu>
      <DropdownMenu.Trigger
        as="button"
        class="btn btn-outline-secondary dropdown-toggle"
        disabled={!props.searches.length}
        title="Recent Searches"
      >
        <Fa icon={faClockRotateLeft} />
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content as="ul" class="dropdown-menu show">
          <For each={props.searches}>
            {(search) => (
              <DropdownMenu.Item as="li">
                <button
                  type="button"
                  class="dropdown-item"
                  onClick={[props.setSearchQuery, search]}
                >
                  {search}
                </button>
              </DropdownMenu.Item>
            )}
          </For>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu>
  );
};
