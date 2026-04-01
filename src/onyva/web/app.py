"""Web application using Bottle."""

from pathlib import Path

from bottle import Bottle, static_file

app = Bottle()

STATIC_DIR = Path(__file__).parent / "static"


@app.route("/")
def index() -> str:
    """Homepage."""
    return "<h1>Hello World</h1>"


@app.route("/static/<filepath:path>")
def serve_static(filepath: str) -> bytes:
    """Serve static files."""
    return static_file(filepath, root=str(STATIC_DIR))


def run() -> None:  # pragma: no cover
    """Run the web application."""
    app.run(host="localhost", port=8080, debug=True)
