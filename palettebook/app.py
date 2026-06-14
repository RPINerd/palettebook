"""Flask application factory for PaletteBook."""

import logging
from pathlib import Path

from flask import Flask, Response, send_from_directory

from .database import init_app
from .routes.colors import bp as colors_bp
from .routes.export import bp as export_bp
from .routes.generate import bp as generate_bp
from .routes.import_csv import bp as import_bp
from .routes.palettes import bp as palettes_bp

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns:
        (Flask): Configured Flask application instance.
    """
    app = Flask(__name__, static_folder=None)

    # Initialise database (creates tables if absent)
    init_app(app)

    # Register API blueprints
    app.register_blueprint(palettes_bp)
    app.register_blueprint(colors_bp)
    app.register_blueprint(generate_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(export_bp)

    # Serve the index page and static assets
    @app.get("/")
    def index() -> Response:
        return send_from_directory(_STATIC_DIR, "index.html")

    @app.get("/<path:filename>")
    def static_files(filename: str) -> Response:
        return send_from_directory(_STATIC_DIR, filename)

    logger.info("PaletteBook application created.")
    return app
