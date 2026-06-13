"""
Entry point for PaletteBook.

Run with:
    uv run python -m palettebook
or:
    uv run palettebook
"""

import argparse
import logging
import logging.handlers
from pathlib import Path

from .app import create_app


def setup_logging(console_level: int = logging.DEBUG) -> None:
    """
    Configure the root logger with a console handler and a rotating file handler.

    Should be called exactly once at application startup, before any other module produces log output.

    Args:
        console_level: Minimum level emitted to the console.
            The file handler always captures DEBUG and above. Defaults to logging.DEBUG.
    """
    Path("logs").mkdir(exist_ok=True)
    log_file = Path("logs/palettebook.log")

    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s %(lineno)d | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # Rotate at 10 MB, keep 5 backups so logs don't consume excessive disk space.
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console_handler)
    root.addHandler(file_handler)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="palettebook",
        description="Locally hosted color palette manager.",
    )
    parser.add_argument("-H", "--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int, default=9070, help="Bind port (default: 9070)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable Flask debug mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    return parser


def main() -> None:
    """Parse CLI arguments and start the development server."""
    args = _build_parser().parse_args()
    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    app = create_app()
    print(f"PaletteBook running at http://{args.host}:{args.port}/")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
