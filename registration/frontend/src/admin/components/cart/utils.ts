import isEqual from "lodash/isEqual";

import type { Badge } from "@admin/api";

export const getBadgeIds = (badges: Badge[]): Set<number> => {
  return new Set(badges.map((badge) => badge.id));
};

export const createAutoPrintCheck = (): ((
  printableIds: number[],
  currentBadges: Badge[],
) => boolean) => {
  let previousBadges: Badge[] = [];

  return function (printableIds: number[], nextBadges: Badge[]): boolean {
    const currentBadges = previousBadges;
    previousBadges = nextBadges;

    if (nextBadges.length === 0 || currentBadges.length !== nextBadges.length) {
      return false;
    }

    for (let i = 0; i < currentBadges.length; i += 1) {
      const prev = currentBadges[i];
      const curr = nextBadges[i];

      if (!printableIds.includes(curr.id)) {
        return false;
      }

      if (
        prev.id !== curr.id ||
        curr.abandoned === prev.abandoned ||
        curr.abandoned !== "Paid"
      ) {
        return false;
      }
    }

    return true;
  };
};

export const createAutoClearCheck = (): ((
  currentBadges: Badge[],
) => boolean) => {
  let previousBadges: Badge[] = [];

  return function (nextBadges: Badge[]): boolean {
    const currentBadges = previousBadges;
    previousBadges = nextBadges;

    if (nextBadges.length === 0 || currentBadges.length !== nextBadges.length) {
      return false;
    }

    const hasSameBadges = isEqual(
      getBadgeIds(currentBadges),
      getBadgeIds(nextBadges),
    );

    const currentHadUnprinted = currentBadges.some((badge) => !badge.printed);
    const nextAllPrinted = nextBadges.every((badge) => badge.printed);

    return hasSameBadges && currentHadUnprinted && nextAllPrinted;
  };
};
