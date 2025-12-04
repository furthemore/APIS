FROM node:lts AS assets

ENV NODE_ENVIRONMENT=production

WORKDIR /app/registration/frontend

COPY ./registration/frontend/package.json ./registration/frontend/package-lock.json /app/registration/frontend/
RUN npm install
COPY ./registration/frontend/ /app/registration/frontend/
RUN npm run build

FROM tiangolo/uwsgi-nginx:python3.11

LABEL org.opencontainers.image.source="https://github.com/furthemore/APIS"

ARG SENTRY_RELEASE=local
ENV SENTRY_RELEASE=${SENTRY_RELEASE}

EXPOSE 80

WORKDIR /app

RUN apt-get update && \
    apt-get -y install python3-psycopg2 ca-certificates

COPY ./requirements.txt /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /app/
COPY ./fm_eventmanager/settings.py.docker /app/fm_eventmanager/settings.py
COPY --from=assets /app/registration/static/ /app/apis/static/

RUN DJANGO_SECRET_KEY=collectstatic ./manage.py collectstatic --noinput --ignore "bundler/*"

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]
