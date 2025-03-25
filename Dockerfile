FROM ghcr.io/furthemore/apis:apis-base-cb35d5b

LABEL org.opencontainers.image.source="https://github.com/furthemore/APIS"

ARG SENTRY_RELEASE=local
ENV SENTRY_RELEASE ${SENTRY_RELEASE}

EXPOSE 80
EXPOSE 443

WORKDIR /app

COPY . /app/
COPY ./convention_event_manager_django_site/settings.py.docker /app/convention_event_manager_django_site/settings.py

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]
