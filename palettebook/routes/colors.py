"""Color management routes for PaletteBook."""

import logging
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request

from ..database import db
from ..models import Color, Palette
from ..utils.color_utils import normalise_to_hex

logger = logging.getLogger(__name__)
bp = Blueprint("colors", __name__, url_prefix="/api/palettes")


@bp.post("/<int:palette_id>/colors")
def add_color(palette_id: int) -> tuple[Response, int]:
    """
    Add a new color to a palette.

    Args:
        palette_id (int): Primary key of the owning palette.

    Request body (JSON):
        value (str): Color in any supported format.
        name (str, optional): Optional label for the color.

    Returns:
        tuple[Response, int]: JSON of the created color and HTTP status code.
    """
    palette = db.get_or_404(Palette, palette_id)
    data = request.get_json(silent=True) or {}
    raw_value = (data.get("value") or "").strip()
    if not raw_value:
        return jsonify({"error": "value is required"}), 400

    try:
        hex_value = normalise_to_hex(raw_value)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    # Assign position after the current last color
    max_pos = db.session.execute(
        db.select(db.func.max(Color.position)).where(Color.palette_id == palette_id)
    ).scalar()
    position = (max_pos or 0) + 1

    color = Color(
        palette_id=palette_id,
        hex_value=hex_value,
        name=(data.get("name") or "").strip() or None,
        position=position,
    )
    db.session.add(color)
    palette.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info("Added color %s to palette %s", hex_value, palette_id)
    return jsonify(color.to_dict()), 201


@bp.put("/<int:palette_id>/colors/<int:color_id>")
def update_color(palette_id: int, color_id: int) -> tuple[Response, int]:
    """
    Update a color's value or label.

    Args:
        palette_id (int): Primary key of the owning palette.
        color_id (int): Primary key of the color.

    Request body (JSON):
        value (str, optional): New color value.
        name (str, optional): New label.

    Returns:
        tuple[Response, int]: JSON of the updated color and HTTP status code.
    """
    palette = db.get_or_404(Palette, palette_id)
    color = db.get_or_404(Color, color_id)
    if color.palette_id != palette_id:
        return jsonify({"error": "Color does not belong to this palette"}), 404

    data = request.get_json(silent=True) or {}

    if "value" in data:
        raw_value = (data["value"] or "").strip()
        try:
            color.hex_value = normalise_to_hex(raw_value)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 422

    if "name" in data:
        color.name = (data["name"] or "").strip() or None

    palette.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info("Updated color %s in palette %s", color.hex_value, palette_id)
    return jsonify(color.to_dict()), 200


@bp.delete("/<int:palette_id>/colors/<int:color_id>")
def delete_color(palette_id: int, color_id: int) -> tuple[Response | str, int]:
    """
    Remove a color from a palette.

    Args:
        palette_id (int): Primary key of the owning palette.
        color_id (int): Primary key of the color.

    Returns:
        tuple[Response | str, int]: HTTP status code and optional message.
    """
    palette = db.get_or_404(Palette, palette_id)
    color = db.get_or_404(Color, color_id)
    if color.palette_id != palette_id:
        return jsonify({"error": "Color does not belong to this palette"}), 404

    db.session.delete(color)
    palette.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info("Deleted color %s from palette %s", color.hex_value, palette_id)
    return "", 204
