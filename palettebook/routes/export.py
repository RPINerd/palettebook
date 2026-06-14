"""
Database export route for PaletteBook.

Exports all palettes and their colors to a TSV file with columns:
    palette_name  color_name  hex  rgb  hsl  hsv  forza
"""

import io
import logging

from flask import Blueprint, Response

from ..database import db
from ..models import Palette
from ..utils.color_utils import to_all_formats

logger = logging.getLogger(__name__)
bp = Blueprint("export", __name__, url_prefix="/api")

_COLUMNS = ["palette_name", "color_name", "hex", "rgb", "hsl", "hsv", "forza"]


@bp.get("/export")
def export_database() -> Response:
    """
    Export every palette and color as a UTF-8 TSV file.

    Returns:
        A text/tab-separated-values file attachment named palettebook_export.tsv.
    """
    buf = io.StringIO()

    # Header row
    buf.write("\t".join(_COLUMNS) + "\n")

    palettes = db.session.scalars(db.select(Palette).order_by(Palette.name)).all()
    for palette in palettes:
        for color in palette.colors:
            try:
                fmts = to_all_formats(color.hex_value)
            except ValueError:
                fmts = {"hex": color.hex_value, "rgb": "", "hsl": "", "hsv": "", "forza": ""}

            row = [
                palette.name,
                color.name or "",
                fmts.get("hex", ""),
                fmts.get("rgb", ""),
                fmts.get("hsl", ""),
                fmts.get("hsv", ""),
                fmts.get("forza", ""),
            ]
            buf.write("\t".join(row) + "\n")

    logger.info("Exported %d palettes to TSV", len(palettes))

    return Response(
        buf.getvalue(),
        mimetype="text/tab-separated-values",
        headers={"Content-Disposition": "attachment; filename=palettebook_export.tsv"},
    )
