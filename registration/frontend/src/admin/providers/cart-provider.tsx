import isEqual from "lodash/isEqual";
import {
  type Accessor,
  createContext,
  createSignal,
  onCleanup,
} from "solid-js";

const storageKey = (terminalId: number) => `apis:onsite:cart:${terminalId}`;

const parseStored = (raw: string | null): number[] => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed.filter((id): id is number => typeof id === "number");
    }
  } catch (err) {
    console.error(`Could not parse stored cart: ${err}`);
  }
  return [];
};

export class CartStore {
  public readonly badgeIds: Accessor<number[]>;
  private readonly setBadgeIds: (ids: number[]) => number[];
  private readonly storageKey: string;

  constructor(terminalId: number) {
    this.storageKey = storageKey(terminalId);

    const [badgeIds, setBadgeIds] = createSignal<number[]>(
      parseStored(globalThis.localStorage.getItem(this.storageKey)),
      { equals: isEqual },
    );
    this.badgeIds = badgeIds;
    this.setBadgeIds = setBadgeIds;

    const onStorage = (ev: StorageEvent) => {
      if (ev.key === this.storageKey) {
        setBadgeIds(parseStored(ev.newValue));
      }
    };

    globalThis.addEventListener("storage", onStorage);
    onCleanup(() => globalThis.removeEventListener("storage", onStorage));
  }

  private commit(ids: number[]) {
    this.setBadgeIds(ids);
    globalThis.localStorage.setItem(this.storageKey, JSON.stringify(ids));
  }

  add(ids: number[]) {
    const current = this.badgeIds();
    const merged = current.slice();
    for (const id of ids) {
      if (!merged.includes(id)) merged.push(id);
    }
    if (merged.length !== current.length) this.commit(merged);
  }

  replace(ids: number[]) {
    if (!isEqual(this.badgeIds(), ids)) this.commit(ids.slice());
  }

  remove(id: number) {
    const current = this.badgeIds();
    if (current.includes(id)) {
      this.commit(current.filter((existing) => existing !== id));
    }
  }

  clear() {
    if (this.badgeIds().length > 0) this.commit([]);
  }
}

export const CartContext = createContext<Accessor<CartStore>>();
