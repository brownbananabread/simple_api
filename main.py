import os

from simple_api import flask

SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "3000"))
AUTO_SAVE = os.environ.get("AUTO_SAVE", "false").lower() == "true"
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# Create app instance for gunicorn
app = flask.create_app()

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

        print(f"Starting production server on {SERVER_HOST}:{SERVER_PORT} with {options['workers']} workers")
        StandaloneApplication(app, options).run()
    else:
        # Development mode: use Flask's built-in server
        print(f"Starting development server on {SERVER_HOST}:{SERVER_PORT}")
        app.run(host=SERVER_HOST, port=SERVER_PORT, debug=AUTO_SAVE)
