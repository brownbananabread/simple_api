import os
import pathlib
from functools import wraps

import requests
from flask import Flask, session, abort, redirect, request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask("Google Login App")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY")

# Allow HTTP traffic for local development (disable in production)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = os.environ.get("OAUTHLIB_INSECURE_TRANSPORT", "1")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost/callback")

if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID environment variable is not set")

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

if not os.path.exists(client_secrets_file):
    raise FileNotFoundError(
        f"client_secret.json not found at {client_secrets_file}. "
        f"Please copy client_secret.json.example to client_secret.json and fill in your credentials."
    )

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_uri=REDIRECT_URI
)


def login_is_required(function):
    """Decorator to require login for protected routes."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function(*args, **kwargs)
    return wrapper


@app.route("/login")
def login():
    """Initiate the OAuth login flow."""
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    """Handle the OAuth callback from Google."""
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    return redirect("/protected_area")


@app.route("/logout")
def logout():
    """Log out the current user."""
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    """Home page with login button."""
    return "Hello World <a href='/login'><button>Login</button></a>"


@app.route("/protected_area")
@login_is_required
def protected_area():
    """Protected area that requires authentication."""
    return f"Hello {session['name']} {session['email']}! <br/> <a href='/logout'><button>Logout</button></a>"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
