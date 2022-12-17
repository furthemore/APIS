FROM ghcr.io/furthemore/apis:apis-base-4849cb3

LABEL org.opencontainers.image.source="https://github.com/furthemore/APIS"

ARG SENTRY_RELEASE=local
ENV SENTRY_RELEASE ${SENTRY_RELEASE}

EXPOSE 80
EXPOSE 443

WORKDIR /app

COPY . /app/
COPY ./fm_eventmanager/settings.py.docker /app/fm_eventmanager/settings.py

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]
