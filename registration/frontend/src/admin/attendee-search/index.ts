import { ApisUrls, CSRF_TOKEN } from "../../entrypoints/admin";
import { AttendeeSearch } from "./components/AttendeeSearch";

export { AttendeeSearch };

export interface BadgeResult {
  id: number;
  edit_url: string;
  attendee: Attendee;
  badgeName: string;
  abandoned: string;
}

export interface Attendee {
  firstName: string;
  lastName: string;
  preferredName?: string;
}

export async function getSearchResults(
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
