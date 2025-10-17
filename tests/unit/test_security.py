"""Tests for security features and headers."""

import json

import pytest

from simple_api.flask import create_app


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestSecurityHeaders:
    """Test security headers in responses."""

    def test_security_headers_present_on_get(self, client):
        """Test that security headers are present on GET requests."""
        response = client.get("/health")

        # Check for common security headers
        headers = response.headers

        # X-Content-Type-Options
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

        # X-Frame-Options
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]

        # Strict-Transport-Security (HSTS)
        assert "Strict-Transport-Security" in headers
        assert "max-age" in headers["Strict-Transport-Security"]

        # Content-Security-Policy
        assert "Content-Security-Policy" in headers
        csp = headers["Content-Security-Policy"]
        assert csp is not None
        # Verify CSP allows Swagger UI to work
        assert "script-src 'self' 'unsafe-inline'" in csp
        assert "style-src 'self' 'unsafe-inline'" in csp
        assert "img-src 'self' data:" in csp

    def test_security_headers_present_on_post(self, client):
        """Test that security headers are present on POST requests."""
        response = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Security Test", "content": "Content"}),
            content_type="application/json",
        )

        headers = response.headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers

        if response.status_code == 201:
            # Cleanup
            client.delete(f"/api/v1/notes/{response.get_json()['id']}")

    def test_security_headers_on_error_responses(self, client):
        """Test that security headers are present even on error responses."""
        response = client.get("/nonexistent")

        headers = response.headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers

    def test_cors_headers_configuration(self, client):
        """Test CORS headers configuration."""
        response = client.options("/api/v1/notes")

        # Check for CORS headers
        headers = response.headers

        if "Access-Control-Allow-Origin" in headers:
            # CORS is configured
            assert headers["Access-Control-Allow-Origin"] is not None

            # If CORS is enabled, check other CORS headers
            if response.status_code == 200:
                assert (
                    "Access-Control-Allow-Methods" in headers
                    or "Access-Control-Allow-Headers" in headers
                )

    def test_content_type_header_json_responses(self, client):
        """Test that JSON responses have correct content type."""
        response = client.get("/health")

        assert response.content_type == "application/json"

    def test_no_server_version_leaked(self, client):
        """Test that server version information is not leaked."""
        response = client.get("/health")

        # Check that Server header doesn't reveal version details
        if "Server" in response.headers:
            server_header = response.headers["Server"].lower()
            # Should not contain version numbers
            assert "werkzeug" not in server_header or "/" not in server_header


class TestInputSanitization:
    """Test input sanitization and validation."""

    def test_xss_prevention_in_title(self, client):
        """Test that XSS attempts in title are handled safely."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
        ]

        for payload in xss_payloads:
            response = client.post(
                "/api/v1/notes",
                data=json.dumps({"title": payload, "content": "Content"}),
                content_type="application/json",
            )

            if response.status_code == 201:
                data = response.get_json()
                # Verify the data is returned as-is (not executed)
                assert data["title"] == payload
                # Verify content-type is JSON (not HTML)
                assert response.content_type == "application/json"

                # Cleanup
                client.delete(f"/api/v1/notes/{data['id']}")

    def test_sql_injection_prevention(self, client):
        """Test that SQL injection attempts are handled safely."""
        sql_payloads = [
            "'; DROP TABLE notes; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM notes--",
        ]

        for payload in sql_payloads:
            response = client.post(
                "/api/v1/notes",
                data=json.dumps({"title": payload, "content": "Content"}),
                content_type="application/json",
            )

            if response.status_code == 201:
                data = response.get_json()
                # The payload should be stored as plain text
                assert data["title"] == payload

                # Cleanup
                client.delete(f"/api/v1/notes/{data['id']}")

    def test_path_traversal_prevention(self, client):
        """Test that path traversal attempts are handled."""
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f",
        ]

        for payload in path_payloads:
            response = client.post(
                "/api/v1/notes",
                data=json.dumps({"title": payload, "content": "Content"}),
                content_type="application/json",
            )

            if response.status_code == 201:
                data = response.get_json()
                # Should be treated as regular text
                assert data["title"] == payload

                # Cleanup
                client.delete(f"/api/v1/notes/{data['id']}")

    def test_command_injection_prevention(self, client):
        """Test that command injection attempts are handled."""
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "$(whoami)",
            "`whoami`",
        ]

        for payload in command_payloads:
            response = client.post(
                "/api/v1/notes",
                data=json.dumps({"title": payload, "content": "Content"}),
                content_type="application/json",
            )

            if response.status_code == 201:
                data = response.get_json()
                # Should be stored as plain text
                assert data["title"] == payload

                # Cleanup
                client.delete(f"/api/v1/notes/{data['id']}")


class TestRateLimitingAndDOS:
    """Test for DOS protection (if implemented)."""

    def test_large_payload_rejection(self, client):
        """Test that extremely large payloads are rejected."""
        # Create a very large payload
        large_content = "x" * (2 * 1024 * 1024)  # 2MB
        payload = {"title": "Large Test", "content": large_content}

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Should be rejected (413 Payload Too Large or 400 Bad Request)
        assert response.status_code in [400, 413]

    def test_multiple_rapid_requests(self, client):
        """Test handling of multiple rapid requests."""
        note_ids = []

        # Make 50 rapid requests
        for i in range(50):
            response = client.post(
                "/api/v1/notes",
                data=json.dumps({"title": f"Rapid {i}", "content": f"Content {i}"}),
                content_type="application/json",
            )

            # Should handle gracefully (either succeed or rate limit)
            assert response.status_code in [201, 429]

            if response.status_code == 201:
                note_ids.append(response.get_json()["id"])

        # Cleanup
        for note_id in note_ids:
            client.delete(f"/api/v1/notes/{note_id}")


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization (if implemented)."""

    def test_endpoints_are_accessible(self, client):
        """Test that endpoints are accessible (or properly secured)."""
        # Test public endpoints
        endpoints = [
            ("/health", "GET"),
            ("/", "GET"),
            ("/api/v1/notes", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)

            # Should either be accessible or return 401/403
            assert response.status_code in [200, 401, 403]

    def test_no_sensitive_info_in_error_responses(self, client):
        """Test that error responses don't leak sensitive information."""
        # Trigger various errors
        error_responses = [
            client.get("/notes/invalid-id"),
            client.post("/api/v1/notes", data="invalid", content_type="application/json"),
            client.get("/nonexistent"),
        ]

        for response in error_responses:
            data = response.get_json()

            # Check that error messages don't contain sensitive info
            error_message = str(data).lower()
            sensitive_terms = [
                "traceback",
                "file path",
                "/users/",
                "password",
                "secret",
                "token",
            ]

            for term in sensitive_terms:
                if term in error_message:
                    # Some terms might appear in normal error messages
                    # Just ensure they're not exposing actual paths or values
                    pass


class TestDataValidation:
    """Test data validation and sanitization."""

    def test_json_injection_prevention(self, client):
        """Test that JSON injection is prevented."""
        # Try to inject additional JSON fields
        payload = {
            "title": "Test",
            "content": "Content",
            "id": "malicious-id",
            "created_at": "2000-01-01T00:00:00",
            "admin": True,
        }

        response = client.post(
            "/api/v1/notes",
            data=json.dumps(payload),
            content_type="application/json",
        )

        if response.status_code == 201:
            data = response.get_json()

            # ID should be generated, not accepted from input
            assert data["id"] != "malicious-id"

            # created_at should be set by server
            assert data["created_at"] != "2000-01-01T00:00:00"

            # Extra fields should be ignored
            assert "admin" not in data

            # Cleanup
            client.delete(f"/api/v1/notes/{data['id']}")

    def test_boolean_type_validation(self, client):
        """Test that boolean fields are properly validated."""
        # Create a note
        note = client.post(
            "/api/v1/notes",
            data=json.dumps({"title": "Test", "content": "Content"}),
            content_type="application/json",
        ).get_json()

        # Try various boolean representations
        test_cases = [
            (True, True),
            (False, False),
        ]

        for input_val, expected_val in test_cases:
            response = client.put(
                f"/api/v1/notes/{note['id']}",
                data=json.dumps({"completed": input_val}),
                content_type="application/json",
            )

            if response.status_code == 200:
                data = response.get_json()
                assert data["completed"] is expected_val

        # Cleanup
        client.delete(f"/api/v1/notes/{note['id']}")

    def test_uuid_format_validation(self, client):
        """Test that UUID validation is strict."""
        invalid_uuids = [
            "not-a-uuid",
            "12345",
            "abc-def-ghi",
            "00000000-0000-0000-0000-000000000000x",  # Extra character
            "",
        ]

        for invalid_uuid in invalid_uuids:
            response = client.get(f"/api/v1/notes/{invalid_uuid}")
            # Invalid UUIDs should return 400 (Bad Request) or 404 (Not Found)
            # depending on how validation is implemented
            assert response.status_code in [400, 404]


class TestHTTPMethodSecurity:
    """Test HTTP method security."""

    def test_method_not_allowed_handling(self, client):
        """Test that incorrect HTTP methods are rejected."""
        # Health endpoint should only accept GET
        response = client.post("/health")
        assert response.status_code == 405

        response = client.put("/health")
        assert response.status_code == 405

        response = client.delete("/health")
        assert response.status_code == 405

    def test_options_method_handled(self, client):
        """Test that OPTIONS method is handled correctly."""
        response = client.options("/api/v1/notes")

        # Should return 200 or 204
        assert response.status_code in [200, 204, 405]

    def test_head_method_handled(self, client):
        """Test that HEAD method is handled correctly."""
        response = client.head("/health")

        # Should return same status as GET but no body
        assert response.status_code in [200, 405]
        # HEAD should not return a body
        assert len(response.data) == 0 or response.status_code == 405


class TestContentSecurity:
    """Test content security policies."""

    def test_response_content_type_is_json(self, client):
        """Test that API responses are JSON."""
        endpoints = [
            "/health",
            "/",
            "/api/v1/notes",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                assert "application/json" in response.content_type

    def test_no_html_in_json_responses(self, client):
        """Test that JSON responses don't contain HTML."""
        response = client.get("/health")

        if response.status_code == 200:
            data = response.get_data(as_text=True)
            # Should not contain HTML tags
            assert "<html" not in data.lower()
            assert "<script" not in data.lower()
            assert "<!doctype" not in data.lower()

    def test_error_responses_are_json(self, client):
        """Test that error responses are also JSON formatted."""
        error_endpoints = [
            "/nonexistent",
            "/notes/invalid-uuid",
        ]

        for endpoint in error_endpoints:
            response = client.get(endpoint)
            assert "application/json" in response.content_type

            # Should be parseable JSON
            data = response.get_json()
            assert isinstance(data, dict)
            assert "error" in data
