"""
CSV/TSV palette import route for PaletteBook.

Expected file format (header row optional):

    palette_name, color_name, <color_col_1>, <color_col_2>, ...

- Column 0: Palette name. Rows sharing a name are grouped into one palette.
    If a palette with that name already exists in the DB it will be reused.
- Column 1: Color label (optional, may be empty).
- Columns 2+: Color values in any supported format; hex, rgb, hsl, hsv, cmyk
    The first column per row that successfully parses is used; the rest are ignored.

Both comma-separated (.csv) and tab-separated (.tsv / .txt) files are accepted. The delimiter is detected
    automatically from the file content. A UTF-8 BOM is stripped if present.
"""

import csv
import io
import logging

from flask import Blueprint, Response, jsonify, request

from ..database import db
from ..models import Color, Palette
from ..utils.color_utils import normalise_to_hex

logger = logging.getLogger(__name__)
bp = Blueprint("import_csv", __name__, url_prefix="/api")


def _detect_delimiter(sample: str) -> str:
    """
    Return the most likely field delimiter in {sample}

    Args:
        sample (str): A short prefix of the file content used for sniffing.

    Returns:
        str: backslash-t for tab-separated, comma for comma-separated.
    """
    return "\t" if sample.count("\t") > sample.count(",") else ","


def _try_parse(value: str) -> str | None:
    """
    Attempt to parse {value} as a color.

    Args:
        value (str): Raw cell string.

    Returns:
        str | None: Lowercase hex string on success, None if the value cannot be parsed.
    """
    value = value.strip()
    if not value:
        return None
    try:
        return normalise_to_hex(value)
    except ValueError:
        return None


@bp.post("/import")
def import_palette_file() -> tuple[Response, int]:  # noqa: C901, PLR0912, PLR0914, PLR0915
    """
    Import one or more palettes from a CSV or TSV file.

    The request must be multipart/form-data with a single field named
    file containing the upload.

    Returns:
        tuple[Response, int]: JSON summary and status code
            {
                "created_palettes": int,
                "reused_palettes":  int,
                "added_colors":     int,
                "skipped_rows":     int,
                "palettes":         [ <palette> ... ]
            }
    """
    if "file" not in request.files:
        return jsonify({"error": "No file field in request"}), 400

    upload = request.files["file"]
    if not upload.filename:
        return jsonify({"error": "Empty filename"}), 400

    try:
        raw = upload.read().decode("utf-8-sig")  # strip BOM if present
    except UnicodeDecodeError:
        return jsonify({"error": "File must be UTF-8 encoded"}), 422

    delimiter = _detect_delimiter(raw[:4096])
    rows = list(csv.reader(io.StringIO(raw), delimiter=delimiter))

    if not rows:
        return jsonify({"error": "File is empty"}), 422

    # Auto-detect header row
    # If the first cell of the first row cannot be parsed as a color it is almost certainly a header label.
    is_header = _try_parse(rows[0][0]) is None
    data_rows = rows[1:] if is_header else rows

    # Import loop
    # -----------------------------------------------------------------------
    palette_cache: dict[str, Palette] = {}   # name -> model instance
    position_counters: dict[int, int] = {}   # palette_id -> next position
    created_palettes = 0
    reused_palettes = 0
    added_colors = 0
    skipped_rows = 0

    for row in data_rows:
        # Need at least palette name + color label + one color column
        if len(row) < 3:  # noqa: PLR2004
            skipped_rows += 1
            continue

        palette_name = row[0].strip()
        color_label = row[1].strip() or None
        color_columns = row[2:]

        if not palette_name:
            skipped_rows += 1
            continue

        # Find or create palette ---------------------------------------------
        if palette_name not in palette_cache:
            existing = db.session.scalars(
                db.select(Palette).where(Palette.name == palette_name)
            ).first()
            if existing:
                palette_cache[palette_name] = existing
                reused_palettes += 1
            else:
                new_palette = Palette(name=palette_name)
                db.session.add(new_palette)
                db.session.flush()  # obtain auto-generated id immediately
                palette_cache[palette_name] = new_palette
                created_palettes += 1

        palette = palette_cache[palette_name]

        # Resolve next insert position (cached per palette) ------------------
        if palette.id not in position_counters:
            max_pos = db.session.execute(
                db.select(db.func.max(Color.position)).where(
                    Color.palette_id == palette.id
                )
            ).scalar()
            position_counters[palette.id] = (max_pos or 0) + 1

        # Parse first valid color column -------------------------------------
        hex_value = None
        for cell in color_columns:
            hex_value = _try_parse(cell)
            if hex_value:
                break

        if not hex_value:
            skipped_rows += 1
            continue

        db.session.add(
            Color(
                palette_id=palette.id,
                hex_value=hex_value,
                name=color_label,
                position=position_counters[palette.id],
            )
        )
        position_counters[palette.id] += 1
        added_colors += 1

    db.session.commit()

    # Refresh cached palette objects so color_count is accurate
    imported_palettes = []
    for palette in palette_cache.values():
        db.session.refresh(palette)
        imported_palettes.append(palette.to_dict())

    logger.info(
        "Import complete: %d new palettes, %d reused, %d colors added, %d skipped",
        created_palettes,
        reused_palettes,
        added_colors,
        skipped_rows,
    )

    return jsonify(
        {
            "created_palettes": created_palettes,
            "reused_palettes": reused_palettes,
            "added_colors": added_colors,
            "skipped_rows": skipped_rows,
            "palettes": imported_palettes,
        }
    ), 201
