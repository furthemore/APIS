import { ApisUrls } from "../../entrypoints/admin";
import { api } from "../api";
import { AttendeeSearch } from "./components/AttendeeSearch";

export { AttendeeSearch };

export interface BadgeResult {
  id: number;
  editUrl: string;
  attendee: Attendee;
  badgeName: string;
  badgeNumber?: number;
  abandoned: string;
}

export interface Attendee {
  firstName: string;
  lastName: string;
  preferredName?: string;
}

export async function getSearchResults(
  urls: ApisUrls,
  query: string,
): Promise<BadgeResult[]> {
  // Clear results if we search for an empty string.
  if (query.trim().length === 0) {
    return [];
  }

  const data = await api
    .get(urls.onsite_admin_search, {
      searchParams: { search: query },
    })
    .json<{ results: BadgeResult[] }>();

  return data.results;
}
