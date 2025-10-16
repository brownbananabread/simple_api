from simple_api import flask
from simple_api.utils.metadata import NAME


def test_create_app():
    """Test that the Flask app is created successfully."""
    app = flask.create_app()
    assert app is not None
    assert app.name == "simple_api.flask"


def test_health_endpoint():
    """Test the health check endpoint."""
    app = flask.create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "healthy", "service": NAME}


def test_health_endpoint_wrong_method():
    """Test that the health endpoint only accepts GET requests."""
    app = flask.create_app()
    client = app.test_client()

    response = client.post("/health")
    assert response.status_code == 405
