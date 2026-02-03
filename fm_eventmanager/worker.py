from uvicorn_worker import UvicornWorker


class ApisWorker(UvicornWorker):
    CONFIG_KWARGS = {"lifespan": "off"}
