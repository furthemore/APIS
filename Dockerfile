FROM rechner/apis:apis-base-ca726c5

EXPOSE 80
EXPOSE 443

WORKDIR /app

COPY . /app/
COPY ./fm_eventmanager/settings.py.docker /app/fm_eventmanager/settings.py

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]
