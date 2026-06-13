"""Palette routes for PaletteBook."""

import logging
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request

from ..database import db
from ..models import Palette

logger = logging.getLogger(__name__)
bp = Blueprint("palettes", __name__, url_prefix="/api/palettes")


@bp.get("/")
def list_palettes() -> Response:
    """
    Return all palettes ordered by name.

    Returns:
        JSON array of palette objects (without embedded colors).
    """
    palettes = db.session.scalars(db.select(Palette).order_by(Palette.name)).all()
    return jsonify([p.to_dict() for p in palettes])


@bp.post("/")
def create_palette() -> tuple[Response, int]:
    """
    Create a new palette.

    Request body (JSON):
        name (str): Required. The palette name.

    Returns:
        tuple[Response, int]: JSON of the created palette, 201 on success, 400 if name is missing
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    palette = Palette(name=name)
    db.session.add(palette)
    db.session.commit()
    logger.info(f"Created palette id={palette.id} name={palette.name!r}")
    return jsonify(palette.to_dict(include_colors=True)), 201


@bp.get("/<int:palette_id>")
def get_palette(palette_id: int) -> Response:
    """
    Return a single palette with its colors.

    Args:
        palette_id (int): Primary key of the palette.

    Returns:
        JSON palette object including color list.
    """
    palette = db.get_or_404(Palette, palette_id)
    return jsonify(palette.to_dict(include_colors=True))


@bp.put("/<int:palette_id>")
def update_palette(palette_id: int) -> tuple[Response, int]:
    """
    Rename a palette.

    Args:
        palette_id (int): Primary key of the palette.

    Request body (JSON):
        name (str): New palette name.

    Returns:
        tuple[Response, int]: JSON of the updated palette, 200 on success, 400 if name is missing.
    """
    palette = db.get_or_404(Palette, palette_id)
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    palette.name = name
    palette.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(palette.to_dict(include_colors=True)), 200


@bp.delete("/<int:palette_id>")
def delete_palette(palette_id: int) -> tuple[Response | str, int]:
    """
    Delete a palette and all its colors.

    Args:
        palette_id (int): Primary key of the palette.

    Returns:
        tuple[Response | str, int]: 204 No Content on success.
    """
    palette = db.get_or_404(Palette, palette_id)
    db.session.delete(palette)
    db.session.commit()
    logger.info(f"Deleted palette id={palette_id}")
    return "", 204


@bp.post("/<int:palette_id>/colors/reorder")
def reorder_colors(palette_id: int) -> tuple[Response, int]:
    """
    Reorder colors within a palette.

    Args:
        palette_id (int): Primary key of the palette.

    Request body (JSON):
        color_ids (list[int]): Ordered list of color IDs.

    Returns:
        tuple[Response, int]: JSON of the updated palette with colors, 200 on success, 400 if color_ids is invalid.
    """
    palette = db.get_or_404(Palette, palette_id)
    data = request.get_json(silent=True) or {}
    color_ids = data.get("color_ids", [])
    if not isinstance(color_ids, list):
        return jsonify({"error": "color_ids must be a list"}), 400

    id_to_color = {c.id: c for c in palette.colors}
    for position, cid in enumerate(color_ids):
        if cid in id_to_color:
            id_to_color[cid].position = position

    palette.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(palette.to_dict(include_colors=True)), 200
