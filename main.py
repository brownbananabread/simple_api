import os

from simple_api import flask
from simple_api.middleware import logger
from simple_api.utils import metadata

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "3000"))
AUTO_SAVE = os.environ.get("AUTO_SAVE", "false").lower() == "true"
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()

app = flask.create_app()

LOG = logger.setup(level=LOG_LEVEL)

if __name__ == "__main__":
    if ENVIRONMENT == "production":
        # Production mode: use gunicorn
        from gunicorn.app.base import BaseApplication

        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            "bind": f"{SERVER_HOST}:{SERVER_PORT}",
            "workers": int(os.environ.get("WORKERS", "4")),
            "worker_class": "sync",
            "loglevel": os.environ.get("LOG_LEVEL", "info").lower(),
            "accesslog": "-",
            "errorlog": "-",
            "timeout": int(os.environ.get("WORKER_TIMEOUT", "30")),
        }
        LOG.info(
            f"Starting {metadata.NAME} v{metadata.VERSION}(production server): "
            f"host={SERVER_HOST}:{SERVER_PORT}, workers={options['workers']}, "
            f"log_level={LOG_LEVEL}"
        )
        StandaloneApplication(app, options).run()
    else:
        # Development mode: use Flask's built-in server
        LOG.info(
            f"Starting {metadata.NAME} v{metadata.VERSION}(development server): "
            f"host={SERVER_HOST}:{SERVER_PORT}, log_level={LOG_LEVEL}"
        )
        app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)
