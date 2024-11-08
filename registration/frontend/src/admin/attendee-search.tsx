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

import { ConfigContext } from "./providers/config-provider";
import { ApisUrls, CSRF_TOKEN } from "../entrypoints/admin";
import { CartManager } from "./cart/cart-manager";

interface BadgeResult {
  id: number;
  edit_url: string;
  attendee: Attendee;
  badgeName: string;
  abandoned: string;
}

interface Attendee {
  firstName: string;
  lastName: string;
  preferredName?: string;
}

async function getSearchResults(
  urls: ApisUrls,
  query: string
): Promise<BadgeResult[]> {
  // Clear results if we search for an empty string.
  if (query.trim().length === 0) {
    return [];
  }

  let formData = new FormData();
  formData.set("search", query);

  const resp = await fetch(urls.onsite_admin_search, {
    method: "POST",
    body: formData,
    headers: {
      "x-csrftoken": CSRF_TOKEN,
    },
  });
  const data = await resp.json();

  return data["results"];
}

const BadgeTableRow: Component<{
  cartManager: CartManager;
  badge: BadgeResult;
}> = (props) => {
  return (
    <tr>
      <td class="is-vcentered">
        <div>
          {`${props.badge.attendee.firstName} ${props.badge.attendee.lastName}`}
        </div>

        <Show when={props.badge.attendee.preferredName}>
          <div>
            <i>Preferred Name:</i>
            <b>{props.badge.attendee.preferredName}</b>
          </div>
        </Show>
      </td>
      <td class="is-vcentered">{props.badge.badgeName}</td>
      <td class="is-vcentered">{props.badge.abandoned}</td>
      <td class="is-vcentered">
        <div class="buttons is-right">
          <a
            href={props.badge.edit_url}
            target="edit"
            class="button is-small is-info"
          >
            <span class="icon">
              <i class="fas fa-edit"></i>
            </span>
          </a>

          <button
            class="button is-small is-primary"
            onClick={(ev) => {
              ev.preventDefault();
              props.cartManager.addCartId(props.badge.id);
            }}
          >
            <span class="icon">
              <i class="fas fa-plus"></i>
            </span>
          </button>
        </div>
      </td>
    </tr>
  );
};

const BadgeTableLoader: Component = () => {
  return (
    <tr>
      <td class="is-vcentered">
        <div class="is-skeleton">
          <div>Full Name</div>
        </div>
      </td>
      <td class="is-vcentered">
        <div class="is-skeleton">
          <div>Badge Name</div>
        </div>
      </td>
      <td class="is-vcentered">
        <div class="is-skeleton">
          <div>Status</div>
        </div>
      </td>
      <td class="is-vcentered">
        <div class="buttons is-right">
          <a href="#" class="button is-small is-skeleton">
            <span class="icon">
              <i class="fas fa-edit"></i>
            </span>
          </a>

          <button class="button is-small is-skeleton">
            <span class="icon">
              <i class="fas fa-plus"></i>
            </span>
          </button>
        </div>
      </td>
    </tr>
  );
};

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
    if (props.searchQuery()) {
      searchInputRef.value = props.searchQuery();
    }
  });

  return (
    <div class="block">
      <div class="block">
        <div class="panel is-primary">
          <div class="panel-heading">
            <div class="columns">
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
                    placeholder="Search attendees"
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
                <Show when={!results.loading} fallback={<BadgeTableLoader />}>
                  <Show
                    when={results()?.length > 0}
                    fallback={
                      <tr>
                        <td colSpan={4}>No results.</td>
                      </tr>
                    }
                  >
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
