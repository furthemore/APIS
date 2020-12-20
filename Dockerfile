FROM apis:apis-base-905a7da

EXPOSE 80
EXPOSE 443

WORKDIR /app

COPY . /app/
COPY ./fm_eventmanager/settings.py.docker /app/fm_eventmanager/settings.py

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]
