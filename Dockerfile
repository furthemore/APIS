FROM ghcr.io/furthemore/apis:apis-base-985940a

LABEL org.opencontainers.image.source https://github.com/furthemore/APIS

EXPOSE 80
EXPOSE 443

WORKDIR /app

COPY . /app/
COPY ./fm_eventmanager/settings.py.docker /app/fm_eventmanager/settings.py

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]
