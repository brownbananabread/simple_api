"""Swagger/OpenAPI configuration for the API."""

from simple_api.utils import metadata

CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/",
}

TEMPLATE = {
    "info": {
        "title": f"{metadata.NAME} - Todo Notes",
        "description": "A simple CRUD API for managing todo notes",
        "version": metadata.VERSION,
    }
}
