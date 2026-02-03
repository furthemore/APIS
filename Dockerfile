FROM node:lts AS assets

ENV NODE_ENVIRONMENT=production

WORKDIR /app/registration/frontend

COPY ./registration/frontend/package.json ./registration/frontend/package-lock.json /app/registration/frontend/
RUN npm install
COPY ./registration/frontend/ /app/registration/frontend/
RUN node esbuild.mjs

FROM python:3.13-slim-trixie

LABEL org.opencontainers.image.source="https://github.com/furthemore/APIS"

ARG SENTRY_RELEASE=local
ENV SENTRY_RELEASE=${SENTRY_RELEASE}

EXPOSE 80 81

RUN useradd --shell /bin/bash --create-home --home /app --uid 1000 apis

WORKDIR /app

RUN apt-get update && \
    apt-get install --no-install-recommends -y git nginx supervisor && \
    apt-get clean

RUN mkdir -p /var/lib/nginx /app/log/nginx && \
    chown -R apis /var/lib/nginx /app/log/nginx

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

USER apis

RUN --mount=type=cache,mode=0755,uid=1000,target=/app/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY --chown=apis . /app/
COPY --chown=apis ./fm_eventmanager/settings.py.docker /app/fm_eventmanager/settings.py
COPY --from=assets --chown=apis /app/registration/static/ /app/registration/static/

RUN --mount=type=cache,mode=0755,uid=1000,target=/app/.cache/uv \
    uv sync --frozen

RUN DJANGO_SECRET_KEY=collectstatic uv run ./manage.py collectstatic --noinput

CMD ["/app/start.sh"]
