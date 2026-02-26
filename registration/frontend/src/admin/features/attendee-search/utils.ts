import type { BadgeResult } from "@admin/api";

export const hasAnyExactMatch = (
  query: string,
  badge: BadgeResult,
): boolean => {
  const fullName = `${badge.attendee.firstName.trim()} ${badge.attendee.lastName.trim()}`;
  const preferredName = `${badge.attendee.preferredName?.trim()} ${badge.attendee.lastName.trim()}`;

  if (
    fullName.localeCompare(query, undefined, {
      sensitivity: "base",
    }) === 0
  ) {
    return true;
  }

  if (
    badge.attendee.preferredName &&
    preferredName.localeCompare(query, undefined, {
      sensitivity: "base",
    }) === 0
  ) {
    return true;
  }

  if (
    badge.badgeName
      .trim()
      .localeCompare(query, undefined, { sensitivity: "base" }) === 0
  ) {
    return true;
  }

  return false;
};
