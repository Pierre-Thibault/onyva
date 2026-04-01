"""BDD tests for web application."""

from pytest_bdd import given, parsers, scenario, then, when
from webtest import TestApp
from webtest.response import TestResponse


@scenario("features/web.feature", "Visit homepage")
def test_visit_homepage() -> None:
    """Test visiting the homepage."""


@given("the web app is running", target_fixture="client")
def web_app() -> TestApp:
    """Create test client."""
    from onyva.web.app import app

    return TestApp(app)


@when(parsers.parse('I visit "{path}"'), target_fixture="response")
def visit_path(client: TestApp, path: str) -> TestResponse:
    """Visit a path."""
    return client.get(path)


@then(parsers.parse('I should see "{text}"'))
def should_see_text(response: TestResponse, text: str) -> None:
    """Check response contains text."""
    assert text in response.text
