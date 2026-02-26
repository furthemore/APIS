import type { UseQueryResult } from "@tanstack/solid-query";
import {
  type Component,
  For,
  Show,
  createMemo,
  createSelector,
  useContext,
} from "solid-js";

import type { BadgeResult } from "@admin/api";
import { UserSettingsContext } from "@admin/providers/user-settings-provider";

import { BadgeTableLoader } from "./badge-table-loader";
import { BadgeTableRow } from "./badge-table-row";

const DEFAULT_SEARCH_RESULTS = 3;

export type AttendeeTableProps = {
  searchQuery: string;
  attendees: UseQueryResult<BadgeResult[], Error>;
  idsInCart: number[];
  selectedAttendee?: number;
};

export const AttendeeTable: Component<AttendeeTableProps> = (props) => {
  const userSettings = useContext(UserSettingsContext)!;
  const showSearchStatus = () =>
    userSettings().settings().showSearchStatus || false;

  const attendeeIdSelector = createSelector(() => props.selectedAttendee);

  const attendeesWhenSearching = createMemo((previous: number) => {
    props.searchQuery;

    const length =
      (props.attendees.isFetched && props.attendees.data?.length) || 0;
    return length > 0 ? length : previous;
  }, DEFAULT_SEARCH_RESULTS);

  const noResults = (
    <tr>
      <td colSpan={4}>No results.</td>
    </tr>
  );

  return (
    <div class="table-responsive attendee-table">
      <table class="table-striped table-hover table align-baseline">
        <thead>
          <tr class="sticky-top z-1">
            <th style={{ width: "35%" }}>Name</th>
            <th style={{ width: showSearchStatus() ? "40%" : "50%" }}>Badge</th>
            <Show when={showSearchStatus()}>
              <th style={{ width: "10%" }}>Status</th>
            </Show>
            <th style={{ width: "15%" }} />
          </tr>
        </thead>
        <tbody>
          <Show
            when={!props.attendees.isFetching}
            fallback={<BadgeTableLoader count={attendeesWhenSearching()} />}
          >
            <For each={props.attendees.data} fallback={noResults}>
              {(badge, index) => (
                <BadgeTableRow
                  selected={attendeeIdSelector(index())}
                  badge={badge}
                  inCart={props.idsInCart.includes(badge.id)}
                  showStatus={showSearchStatus()}
                  searchQuery={props.searchQuery}
                />
              )}
            </For>
          </Show>
        </tbody>
      </table>
    </div>
  );
};
