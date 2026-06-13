"""SQLAlchemy database setup for PaletteBook"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):

    """Explicit declarative base, allowing Pylance to resolve model attributes."""


db = SQLAlchemy(model_class=Base)

# SQLite file will live next to the package root
_DB_PATH = Path(__file__).parent.parent / "data.db"


def init_app(app: "Flask") -> None:
    """
    Initialise/Load the database of color palettes.

    Args:
        app (Flask): The Flask application instance.
    """
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI", f"sqlite:///{_DB_PATH}"
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db.init_app(app)

    with app.app_context():
        db.create_all()
