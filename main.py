import os

from simple_api.flask import app

SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "3000"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
AUTO_SAVE = os.environ.get("AUTO_SAVE", "false").lower() == "true"

if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=AUTO_SAVE)
