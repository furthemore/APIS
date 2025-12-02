import type { UseQueryResult } from "@tanstack/solid-query";
import {
  type Component,
  For,
  Suspense,
  createMemo,
  createSelector,
} from "solid-js";

import type { BadgeResult } from "@admin/api";

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
            <th style={{ width: "40%" }}>Badge</th>
            <th style={{ width: "10%" }}>Status</th>
            <th style={{ width: "15%" }} />
          </tr>
        </thead>
        <tbody>
          <Suspense
            fallback={<BadgeTableLoader count={attendeesWhenSearching()} />}
          >
            <For each={props.attendees.data} fallback={noResults}>
              {(badge, index) => (
                <BadgeTableRow
                  selected={attendeeIdSelector(index())}
                  badge={badge}
                  inCart={props.idsInCart.includes(badge.id)}
                  searchQuery={props.searchQuery}
                />
              )}
            </For>
          </Suspense>
        </tbody>
      </table>
    </div>
  );
};
