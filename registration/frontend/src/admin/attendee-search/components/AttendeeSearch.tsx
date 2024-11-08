import {
  Accessor,
  Component,
  createEffect,
  createResource,
  For,
  Setter,
  Show,
  useContext,
} from "solid-js";

import { BadgeTableLoader } from "./BadgeTableLoader";
import { BadgeTableRow } from "./BadgeTableRow";
import { CartManager } from "../../cart";
import { ConfigContext } from "../../providers/config-provider";
import { getSearchResults } from "..";

export const AttendeeSearch: Component<{
  cartManager: CartManager;
  searchQuery: Accessor<string>;
  setSearchQuery: Setter<string>;
}> = (props) => {
  const config = useContext(ConfigContext);

  const [results, { refetch }] = createResource(props.searchQuery, (query) =>
    getSearchResults(config.urls, query)
  );

  let searchInputRef: HTMLInputElement;

  createEffect(() => {
    const query = props.searchQuery();

    if (query) {
      searchInputRef.value = query;
    }
  });

  const noResults = (
    <tr>
      <td colSpan={4}>No results.</td>
    </tr>
  );

  return (
    <div class="block">
      <div class="block">
        <div class="panel is-primary">
          <div class="panel-heading">
            <div class="columns is-mobile">
              <div class="column">Attendee Search</div>

              <div class="column is-narrow">
                <a
                  href={config.urls.onsite}
                  target="edit"
                  class="button is-link is-light is-small"
                >
                  Add
                </a>
              </div>
            </div>
          </div>

          <div class="panel-block">
            <form
              class="control"
              onSubmit={(ev) => {
                ev.preventDefault();
                props.setSearchQuery(searchInputRef.value);
              }}
            >
              <div class="field is-grouped">
                <p class="control is-expanded">
                  <input
                    type="search"
                    name="search"
                    class="input"
                    placeholder="Enter names, badge names, and badge numbers"
                    autofocus={true}
                    autocomplete="off"
                    ref={searchInputRef}
                    onInput={(ev) => {
                      if (ev.target.value.length === 0) {
                        props.setSearchQuery("");
                      }
                    }}
                  />
                </p>

                <p class="control">
                  <button
                    class="button is-info"
                    classList={{ "is-loading": results.loading }}
                    type="submit"
                    onClick={() => {
                      refetch(searchInputRef.value);
                    }}
                  >
                    <span class="icon">
                      <i class="fas fa-search"></i>
                    </span>
                  </button>
                </p>
              </div>
            </form>
          </div>

          <div class="panel-block px-0 pt-0">
            <table class="table is-striped is-fullwidth">
              <thead>
                <tr>
                  <th style="width: 35%;">Legal Name</th>
                  <th style="width: 25%;">Badge Name</th>
                  <th style="width: 15%;">Status</th>
                  <th style="width: 25%;"></th>
                </tr>
              </thead>
              <tbody>
                <Show
                  when={!results.loading}
                  fallback={<BadgeTableLoader count={3} />}
                >
                  <Show when={results()?.length > 0} fallback={noResults}>
                    <For each={results()}>
                      {(badge, index) => (
                        <BadgeTableRow
                          data-index={index()}
                          badge={badge}
                          cartManager={props.cartManager}
                        />
                      )}
                    </For>
                  </Show>
                </Show>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
