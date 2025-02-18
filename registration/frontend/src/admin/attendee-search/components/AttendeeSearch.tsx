import { createShortcut } from "@solid-primitives/keyboard";
import {
  Accessor,
  Component,
  createEffect,
  createResource,
  createSignal,
  For,
  Setter,
  Show,
  useContext,
} from "solid-js";

import { getSearchResults } from "..";
import { SentryErrorBoundary } from "../../../entrypoints/admin";
import { CartManager } from "../../cart";
import { ConfigContext } from "../../providers/config-provider";
import { BadgeTableLoader } from "./BadgeTableLoader";
import { BadgeTableRow } from "./BadgeTableRow";

export const AttendeeSearch: Component<{
  cartManager: CartManager;
  searchQuery: Accessor<string | undefined>;
  setSearchQuery: Setter<string | undefined>;
}> = (props) => {
  const config = useContext(ConfigContext)!;

  const [selectedResult, setSelectedResult] = createSignal<number>();
  const [recentSearches, setRecentSearches] = createSignal<string[]>([], {
    equals: false,
  });

  const [results, { refetch }] = createResource(
    props.searchQuery,
    async (query) => await getSearchResults(config.urls, query)
  );

  let searchInputRef!: HTMLInputElement;

  createEffect(() => {
    const query = props.searchQuery();

    if (query !== undefined) {
      searchInputRef.value = query;

      if (query.length > 0) {
        let searches = recentSearches();

        if (searches.length > 0 && searches[0] === query) return;

        searches.unshift(query);
        if (searches.length > 10) searches.length = 10;

        setRecentSearches(searches);
      }
    }
  });

  createEffect(() => {
    const entries = results();
    if (entries && entries.length === 1) {
      setSelectedResult(0);
      if (!props.cartManager.alreadyInCart(entries[0].id)) {
        props.cartManager.addCartId(entries[0].id);
      }
    } else {
      setSelectedResult(undefined);
    }
  });

  createShortcut(["Alt", "F"], () => {
    props.setSearchQuery("");
    searchInputRef.focus();
  });

  createShortcut(["Alt", "."], () => {
    const entries = results();

    if (entries) {
      const selected = selectedResult();
      if (selected) {
        const badge = entries[selected];
        if (badge) {
          props.cartManager.addCartId(badge.id);
          if (selected === entries.length - 1) {
            setSelectedResult(entries.length - 2);
          } else if (selected !== 0) {
            setSelectedResult(selected + 1);
          }
        }
      } else {
        const next = entries.find(
          (badge) => !props.cartManager.alreadyInCart(badge.id)
        );
        if (next) {
          props.cartManager.addCartId(next.id);
        }
      }
    }
  });

  createShortcut(["Alt", "E"], () => {
    const entries = results();
    const selected = selectedResult();

    if (selected && entries?.[selected]) {
      window.open(entries[selected].edit_url, "edit");
    }
  });

  createShortcut(
    ["Control", "E"],
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

          <SentryErrorBoundary
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
                <div class="field has-addons">
                  <div class="control">
                    <div
                      class="dropdown"
                      classList={{ "is-hoverable": !!recentSearches()?.length }}
                    >
                      <div class="dropdown-trigger">
                        <button
                          type="button"
                          class="button"
                          disabled={!recentSearches()?.length}
                          title="Recent Searches"
                        >
                          <span class="icon">
                            <i class="fas fa-clock-rotate-left"></i>
                          </span>
                        </button>
                      </div>
                      <div class="dropdown-menu">
                        <div class="dropdown-content">
                          <For each={recentSearches()}>
                            {(search) => (
                              <a
                                href="#"
                                class="dropdown-item"
                                onClick={(ev) => {
                                  ev.preventDefault();
                                  props.setSearchQuery(search);
                                }}
                              >
                                {search}
                              </a>
                            )}
                          </For>
                        </div>
                      </div>
                    </div>
                  </div>

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
                      onKeyDown={(ev) => {
                        const key = ev.key;
                        if (key !== "ArrowDown" && key !== "ArrowUp") return;

                        ev.preventDefault();

                        const currentlySelected = selectedResult() || 0;
                        const entryCount = results()?.length || 0;

                        switch (ev.key) {
                          case "ArrowDown":
                            if (currentlySelected + 2 <= entryCount) {
                              setSelectedResult(currentlySelected + 1);
                            }
                            break;
                          case "ArrowUp":
                            if (currentlySelected > 0) {
                              setSelectedResult(currentlySelected - 1);
                            }
                            break;
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
                      <th style="width: 35%;">Name</th>
                      <th style="width: 40%;">Badge</th>
                      <th style="width: 10%;">Status</th>
                      <th style="width: 15%;"></th>
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
                              selected={selectedResult() == index()}
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
          </SentryErrorBoundary>
        </div>
      </div>
    </div>
  );
};
