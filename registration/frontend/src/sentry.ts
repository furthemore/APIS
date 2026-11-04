import * as Sentry from "@sentry/solid";
import { createSignal } from "solid-js";

const [currentUser, setCurrentUser] = createSignal<{
  email?: string;
  name?: string;
}>();

const getMetaContent = (name: string): string | undefined =>
  document.querySelector<HTMLMetaElement>(`meta[name='${name}']`)?.content;

const initSentry = () => {
  const sentryDsn = getMetaContent("sentry-dsn");
  if (sentryDsn) {
    Sentry.init({
      dsn: sentryDsn,
      environment: getMetaContent("sentry-environment"),
      release: getMetaContent("sentry-release"),
      beforeSend(event) {
        // Filter out browser extension errors by checking the filename
        const frames = event.exception?.values?.[0]?.stacktrace?.frames;
        if (frames?.some(frame => 
          frame.filename?.includes('webkit-masked-url') ||
          frame.filename?.includes('chrome-extension://') ||
          frame.filename?.includes('moz-extension://') ||
          frame.filename?.includes('safari-extension://')
        )) {
          return null;
        }

        if (event.exception) {
          Sentry.showReportDialog({
            eventId: event.event_id,
            user: currentUser(),
          });
        }

        return event;
      },
    });
  }
};

export { initSentry, setCurrentUser };
