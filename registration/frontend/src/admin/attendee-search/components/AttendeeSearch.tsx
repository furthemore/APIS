import {
  Accessor,
  Component,
  createEffect,
  createResource,
  ErrorBoundary,
  For,
  Setter,
  Show,
  useContext,
} from "solid-js";
import { createShortcut } from "@solid-primitives/keyboard";

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
  const config = useContext(ConfigContext)!;

  const [results, { refetch }] = createResource(
    props.searchQuery,
    async (query) => await getSearchResults(config.urls, query)
  );

  let searchInputRef!: HTMLInputElement;

  createEffect(() => {
    const query = props.searchQuery();

    if (query !== undefined) {
      searchInputRef.value = query;
    }
  });

  createShortcut(["Alt", "F"], () => {
    props.setSearchQuery("");
    searchInputRef.focus();
  });

  createShortcut(["Alt", "."], () => {
    const entries = results();

    if (entries) {
      const next = entries.find(
        (badge) => !props.cartManager.alreadyInCart(badge.id)
      );
      if (next) {
        props.cartManager.addCartId(next.id);
      }
    }
  });

  createShortcut(
    ["Control", "N"],
    () => {
      window.open(config.urls.onsite, "register");
    },
    {
      preventDefault: true,
    }
  );

  const noResults = (
    <tr>
      <td colSpan={4}>No results.</td>
    </tr>
  );

  return (
    <div class="block">
      <div class="block">
        <div class="panel is-dark">
          <div class="panel-heading">
            <div class="columns is-mobile">
              <div class="column is-align-self-center">Attendee Search</div>

              <div class="column is-narrow">
                <a
                  href={config.urls.onsite}
                  target="register"
                  title="Control+N"
                  class="button is-link is-small"
                >
                  <span class="icon">
                    <i class="fas fa-plus"></i>
                  </span>
                  <span>New</span>
                </a>
              </div>
            </div>
          </div>

          <ErrorBoundary
            fallback={(err, reset) => {
              return (
                <div class="panel-block">
                  <div class="message is-danger control">
                    <div class="message-header">
                      <p>Search Error</p>

                      <button
                        class="delete"
                        onClick={() => {
                          props.setSearchQuery("");
                          reset();
                        }}
                      ></button>
                    </div>

                    <Show
                      when={err.toString().length > 0}
                      fallback={
                        <div class="message-body">
                          An unknown error occured.
                        </div>
                      }
                    >
                      <div class="message-body">{err.toString()}</div>
                    </Show>
                  </div>
                </div>
              );
            }}
          >
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
                      placeholder="Enter names or badge number"
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

            <div class="panel-block px-0 py-0">
              <div class="table-container attendee-table">
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
                      <Show
                        when={(results()?.length ?? 0) > 0}
                        fallback={noResults}
                      >
                        <For each={results()}>
                          {(badge, index) => (
                            <BadgeTableRow
                              data-index={index()}
                              badge={badge}
                              cartManager={props.cartManager}
                              searchQuery={props.searchQuery()}
                            />
                          )}
                        </For>
                      </Show>
                    </Show>
                  </tbody>
                </table>
              </div>
            </div>
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
};
