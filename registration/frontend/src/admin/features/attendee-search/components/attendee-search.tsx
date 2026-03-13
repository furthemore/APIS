import {
  faClipboardUser,
  faPeopleLine,
  faPlus,
  faSearch,
} from "@fortawesome/free-solid-svg-icons";
import { createHotkey } from "@tanstack/solid-hotkeys";
import { useQuery } from "@tanstack/solid-query";
import Fa from "solid-fa";
import {
  type Component,
  type Setter,
  createEffect,
  createSignal,
  on,
} from "solid-js";

import { searchAttendeesOptions, useAddBadgeToCart } from "@admin/api";
import { DisplayRegistrationButton } from "@admin/features/display-registration";
import { Button } from "@components/button";
import { IconAndLabel } from "@components/icon-and-label";

import { hasAnyExactMatch } from "../utils";
import { AttendeeTable } from "./attendee-table";
import { RecentSearches } from "./recent-searches";
import { SearchInput } from "./search-input";

export const AttendeeSearch: Component<{
  idsInCart: number[];
  searchQuery: string;
  setSearchQuery: Setter<string>;
}> = (props) => {
  const [searchFieldValue, setSearchFieldValue] = createSignal<string>("");
  const [recentSearches, setRecentSearches] = createSignal<string[]>([]);
  const [selectedAttendee, setSelectedAttendee] = createSignal<number>();

  const attendees = useQuery(() => searchAttendeesOptions(props.searchQuery));
  const addBadgeToCart = useAddBadgeToCart();

  createEffect(() => {
    setSearchFieldValue(props.searchQuery);
  });

  createEffect(() => {
    const query = props.searchQuery;

    if (query.length > 0) {
      const searches = recentSearches().slice(0);

      if (searches.length > 0 && searches[0] === query) return;

      searches.unshift(query);
      if (searches.length > 10) searches.length = 10;

      setRecentSearches(searches);
    }
  });

  createEffect(
    on(
      () => attendees.data,
      (entries) => {
        const searchQuery = props.searchQuery;

        if (entries && entries.length > 0) {
          setSelectedAttendee(0);

          const cleanedSearchQuery = searchQuery
            .replace(/ birthday:(?:[0-9-]{10})/, "")
            .trim();

          const firstResultHasExact = hasAnyExactMatch(
            cleanedSearchQuery,
            entries[0],
          );
          const anyOtherResultHasExact =
            firstResultHasExact &&
            entries
              .slice(1)
              .some((entry) => hasAnyExactMatch(cleanedSearchQuery, entry));

          const hasSingleGoodResult =
            !props.idsInCart.includes(entries[0].id) &&
            firstResultHasExact &&
            !anyOtherResultHasExact;

          const badgeNumMatch = /^num:(\d+)$/.exec(searchQuery.trim());
          const hasMatchingBadgeNum =
            badgeNumMatch &&
            entries.length === 1 &&
            badgeNumMatch[1] === entries[0].badgeNumber?.toString();

          if (hasSingleGoodResult || hasMatchingBadgeNum) {
            addBadgeToCart.mutate(entries[0].id);
          }
        } else {
          setSelectedAttendee(undefined);
        }
      },
    ),
  );

  createHotkey("Alt+.", () => {
    const entries = attendees.data;

    if (entries) {
      const selected = selectedAttendee();
      if (selected) {
        const badge = entries[selected];
        if (badge) {
          addBadgeToCart.mutate(badge.id);
          if (selected === entries.length - 1) {
            setSelectedAttendee(entries.length - 2);
          } else if (selected !== 0) {
            setSelectedAttendee(selected + 1);
          }
        }
      } else {
        const next = entries.find(
          (badge) => !props.idsInCart.includes(badge.id),
        );
        if (next) {
          addBadgeToCart.mutate(next.id);
        }
      }
    }
  });

  createHotkey("Alt+E", () => {
    const entries = attendees.data;
    const selected = selectedAttendee();

    if (selected && entries?.[selected]) {
      globalThis.open(entries[selected].editUrl, "edit");
    }
  });

  createHotkey("Mod+E", () => {
    globalThis.open("/registration/onsite", "register");
  });

  const attendeeCount = () =>
    (attendees.isFetched && attendees.data?.length) || 0;

  const performSearch = (ev: Event) => {
    ev.preventDefault();

    const currentSearch = props.searchQuery;
    if (currentSearch === props.setSearchQuery(searchFieldValue())) {
      attendees.refetch();
    }
  };

  return (
    <div class="card flush-table mb-3">
      <div class="card-header">
        <div class="row align-items-center g-1">
          <div class="col">
            <h5 class="card-heading mb-0">
              <IconAndLabel children="Attendees" icon={faPeopleLine} fw />
            </h5>
          </div>

          <div class="col-auto">
            <DisplayRegistrationButton class="btn btn-secondary btn-sm">
              <IconAndLabel children="Prompt" icon={faClipboardUser} />
            </DisplayRegistrationButton>
          </div>
          <div class="col-auto">
            <a
              href="/registration/onsite"
              target="register"
              title="Control+N"
              class="btn btn-info btn-sm"
            >
              <IconAndLabel children="New" icon={faPlus} />
            </a>
          </div>
        </div>
      </div>

      <div class="card-body">
        <form onSubmit={performSearch}>
          <div class="input-group">
            <RecentSearches
              searches={recentSearches()}
              setSearchQuery={props.setSearchQuery}
            />

            <SearchInput
              value={searchFieldValue()}
              attendeeCount={attendeeCount()}
              selectedAttendee={selectedAttendee()}
              setSearchFieldValue={setSearchFieldValue}
              setSearchQuery={props.setSearchQuery}
              setSelectedAttendee={setSelectedAttendee}
            />

            <Button
              type="submit"
              class="btn btn-outline-primary"
              loading={attendees.isFetching}
              onClick={performSearch}
            >
              <Fa icon={faSearch} />
            </Button>
          </div>
        </form>
      </div>

      <AttendeeTable
        searchQuery={props.searchQuery}
        attendees={attendees}
        idsInCart={props.idsInCart}
        selectedAttendee={selectedAttendee()}
      />
    </div>
  );
};
