if (SENTRY_ENABLED) {
    Sentry.init({
        dsn: SENTRY_FRONTEND_DSN,
        environment: SENTRY_ENVIRONMENT,
        release: SENTRY_RELEASE,
        beforeSend(event, hint) {
            // Check if it is an exception, and if so, show the report dialog
            if (SENTRY_USER_REPORTS && event.exception) {
                Sentry.showReportDialog({eventId: event.event_id});
            }
            return event;
        },
    });
}