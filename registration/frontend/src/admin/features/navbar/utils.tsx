import { toaster } from "@kobalte/core/toast";
import type { UseMutationResult } from "@tanstack/solid-query";
import { Big } from "big.js";

import { ActionToast } from "@components/action-toast";

export const KNOWN_SHORTCUTS = [
  { shortcut: "Alt+O", description: "Open position" },
  { shortcut: "Alt+L", description: "Close position" },
  { shortcut: "Alt+N", description: "Ready for next" },
  { shortcut: "Ctrl+E", description: "Create new attendee" },
  { shortcut: "Ctrl+M", description: "Create new attendee from scanned ID" },
  { shortcut: "Alt+F", description: "Clear results and focus search field" },
  {
    shortcut: "↓",
    description: "While searching, move selection one result down",
  },
  {
    shortcut: "↑",
    description: "While searching, move selection one result up",
  },
  {
    shortcut: "Alt+.",
    description: "Add first eligible or selected search result to cart",
  },
  {
    shortcut: "Alt+E",
    description: "Edit the currently selected search result",
  },
  { shortcut: "Alt+D", description: "Scroll to show all scanner entries" },
  { shortcut: "Alt+S", description: "Clear scanner entries" },
  { shortcut: "Alt+A", description: "Clear cart" },
  { shortcut: "Alt+R", description: "Reload cart" },
  { shortcut: "Alt+\\", description: "Remove last badge from cart" },
  { shortcut: "Alt+M", description: "Tender cash payment" },
  { shortcut: "Alt+C", description: "Prompt for card payment" },
  { shortcut: "Ctrl+P", description: "Print badges in cart" },
];

export const mutateThenToast = <T,>(
  mutation: UseMutationResult<void, Error, T>,
  args: T,
  successMessage: string,
  additionalSuccessAction?: () => void,
) => {
  mutation.mutate(args, {
    onSuccess: () => {
      additionalSuccessAction?.();

      toaster.show((toastProps) => (
        <ActionToast type="success" message={successMessage} {...toastProps} />
      ));
    },
    onError: (err: Error) => {
      toaster.show((toastProps) => (
        <ActionToast type="danger" message={err.toString()} {...toastProps} />
      ));
    },
  });
};

export const amountRequest = (
  mutation: UseMutationResult<void, Error, Big>,
  message: string,
  successMessage?: string,
) => {
  const input = prompt(message);
  if (!input) return;

  let amount: Big;
  try {
    amount = new Big(input);
  } catch {
    alert("Invalid input.");
    return;
  }

  mutateThenToast(mutation, amount, successMessage || "Success");
};
