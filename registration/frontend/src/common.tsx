import * as Sentry from "@sentry/solid";
import { ErrorBoundary } from "solid-js";

export const CSRF_TOKEN = document.querySelector<HTMLMetaElement>(
  "meta[name='csrf_token']",
)!.content;

export const SentryErrorBoundary =
  Sentry.withSentryErrorBoundary(ErrorBoundary);
