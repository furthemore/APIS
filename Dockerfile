FROM node:lts AS assets

ENV NODE_ENVIRONMENT=production

WORKDIR /app/registration/frontend

COPY ./registration/frontend/package.json ./registration/frontend/package-lock.json /app/registration/frontend/
RUN npm install
COPY ./registration/frontend/ /app/registration/frontend/
RUN node esbuild.mjs

FROM ghcr.io/furthemore/apis:apis-base-0a72b3c

LABEL org.opencontainers.image.source="https://github.com/furthemore/APIS"

ARG SENTRY_RELEASE=local
ENV SENTRY_RELEASE=${SENTRY_RELEASE}

EXPOSE 80
EXPOSE 443

WORKDIR /app

COPY . /app/
COPY ./fm_eventmanager/settings.py.docker /app/fm_eventmanager/settings.py
COPY --from=assets /app/registration/static/ /app/registration/static/

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]
