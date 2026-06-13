"""Generation and conversion routes for PaletteBook."""

import logging

from flask import Blueprint, Response, jsonify, request

from ..utils.color_utils import to_all_formats
from ..utils.generators import ALGORITHMS, generate

logger = logging.getLogger(__name__)
bp = Blueprint("generate", __name__, url_prefix="/api")


@bp.get("/algorithms")
def list_algorithms() -> Response:
    """
    Return the available generation algorithm names.

    Returns:
        (Response): JSON array of algorithm name strings.
    """
    return jsonify(list(ALGORITHMS.keys()))


@bp.post("/generate")
def generate_palette() -> tuple[Response, int]:
    """
    Generate a palette from a base color and an algorithm.

    Request body (JSON):
        algorithm (str): Name of the generation algorithm.
        base_color (str, optional): Base color in any supported format.
            Required for all algorithms except random.
        count (int, optional): Number of colors to generate (default 6,
            clamped to 2-20).

    Returns:
        tuple[Response, int]: JSON object with colors (list of hex strings) and
        algorithm (str).
    """
    data = request.get_json(silent=True) or {}
    algorithm = (data.get("algorithm") or "").strip()
    base_color = (data.get("base_color") or "").strip() or None
    count = int(data.get("count") or 6)
    count = max(2, min(20, count))

    if not algorithm:
        return jsonify({"error": "algorithm is required"}), 400

    try:
        colors = generate(algorithm, base_color, count)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    logger.debug("Generated palette with algorithm %r and base color %r: %r", algorithm, base_color, colors)
    return jsonify({"algorithm": algorithm, "colors": colors}), 200


@bp.post("/convert")
def convert_color() -> tuple[Response, int]:
    """
    Convert a color string to all supported formats.

    Request body (JSON):
        value (str): Color in any supported format.

    Returns:
        tuple[Response, int]: JSON object with keys hex, rgb, hsl, hsv, forza.
    """
    data = request.get_json(silent=True) or {}
    value = (data.get("value") or "").strip()
    if not value:
        return jsonify({"error": "value is required"}), 400

    try:
        result = to_all_formats(value)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    logger.debug("Converted color %r to all formats: %r", value, result)
    return jsonify(result), 200
