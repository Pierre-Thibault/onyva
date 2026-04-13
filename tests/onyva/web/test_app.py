"""Tests for the web application."""

from webtest import TestApp

from onyva.web.app import app


def test_serve_static_file() -> None:
    """Test serving static files."""
    client = TestApp(app)
    response = client.get("/static/htmx.min.js")
    assert response.status_int == 200
    assert "htmx" in response.text
