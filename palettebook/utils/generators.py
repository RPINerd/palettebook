"""
Color palette generation algorithms for PaletteBook.

All algorithms accept a base hex color and a target count, and return a list of hex color strings
"""

import colorsys
import random
from collections.abc import Callable

from .color_utils import RGB, hue_shift, normalise_to_hex, parse_color, rgb_to_hex, vary_lightness


def complementary(base_hex: str, count: int = 5) -> list[str]:
    """
    Generate a complementary palette (base + 180 degree opposite + variations).

    Args:
        base_hex (str): Base color in any supported format.
        count (int): Number of colors to return (minimum 2).

    Returns:
        list[str]: List of hex color strings.
    """
    count = max(2, count)
    base = parse_color(base_hex)
    comp = hue_shift(base, 180)
    # Interleave lightness variants of both hues
    half = count // 2
    rest = count - half
    h_base, _, s = colorsys.rgb_to_hsv(base.r, base.g, base.b)
    h_comp, _, _ = colorsys.rgb_to_hsv(comp.r, comp.g, comp.b)

    def _variants(h: float, n: int) -> list[str]:
        out = []
        for i in range(n):
            t = i / max(n - 1, 1)
            v = 0.45 + t * 0.50
            s_ = max(0.35, s)
            r, g, b = colorsys.hsv_to_rgb(h, s_, v)
            out.append(rgb_to_hex(RGB(r, g, b)))
        return out

    return _variants(h_base, rest) + _variants(h_comp, half)


def analogous(base_hex: str, count: int = 5) -> list[str]:
    """
    Generate an 'analogous' palette (neighboring hues both +/-30 and +/-60 degrees).

    Args:
        base_hex (str): Base color in any supported format.
        count (int): Number of colors to return.

    Returns:
        list[str]: List of hex color strings.
    """
    base = parse_color(base_hex)
    h, s, v = colorsys.rgb_to_hsv(base.r, base.g, base.b)
    s = max(0.4, s)
    v = max(0.5, v)
    step = 30.0 / 360
    offsets = [0, -step, step, -2 * step, 2 * step, -3 * step, 3 * step]
    results = []
    for off in offsets[:count]:
        r, g, b = colorsys.hsv_to_rgb((h + off) % 1.0, s, v)
        results.append(rgb_to_hex(RGB(r, g, b)))
    return results


def triadic(base_hex: str, count: int = 6) -> list[str]:
    """
    Generate a triadic, aka triangular, palette (hues at 0/120/240 degrees).

    Args:
        base_hex (str): Base color in any supported format.
        count (int): Number of colors to return.

    Returns:
        list[str]: List of hex color strings.
    """
    base = parse_color(base_hex)
    h, s, v = colorsys.rgb_to_hsv(base.r, base.g, base.b)
    s = max(0.4, s)
    v = max(0.5, v)
    anchors = [h, (h + 1 / 3) % 1.0, (h + 2 / 3) % 1.0]
    results = []
    per_anchor = max(1, count // 3)
    extra = count - per_anchor * 3
    for i, anchor_h in enumerate(anchors):
        slots = per_anchor + (1 if i < extra else 0)
        for j in range(slots):
            v_j = max(0.35, v - 0.15 * j)
            r, g, b = colorsys.hsv_to_rgb(anchor_h, s, v_j)
            results.append(rgb_to_hex(RGB(r, g, b)))
    return results[:count]


def tetradic(base_hex: str, count: int = 8) -> list[str]:
    """
    Generate a tetradic, aka square, palette (hues at 0/90/180/270 degrees).

    Args:
        base_hex (str): Base color in any supported format.
        count (int): Number of colors to return.

    Returns:
        list[str]: List of hex color strings.
    """
    base = parse_color(base_hex)
    h, s, v = colorsys.rgb_to_hsv(base.r, base.g, base.b)
    s = max(0.4, s)
    v = max(0.5, v)
    anchors = [h, (h + 0.25) % 1.0, (h + 0.5) % 1.0, (h + 0.75) % 1.0]
    results = []
    per_anchor = max(1, count // 4)
    extra = count - per_anchor * 4
    for i, anchor_h in enumerate(anchors):
        slots = per_anchor + (1 if i < extra else 0)
        for j in range(slots):
            v_j = max(0.35, v - 0.12 * j)
            r, g, b = colorsys.hsv_to_rgb(anchor_h, s, v_j)
            results.append(rgb_to_hex(RGB(r, g, b)))
    return results[:count]


def split_complementary(base_hex: str, count: int = 6) -> list[str]:
    """
    Generate a split-complementary palette.

    Uses the base hue plus the two colors adjacent to its complement (+/-30 deg).

    Args:
        base_hex (str): Base color in any supported format.
        count (int): Number of colors to return.

    Returns:
        list[str]: List of hex color strings.
    """
    base = parse_color(base_hex)
    h, s, v = colorsys.rgb_to_hsv(base.r, base.g, base.b)
    s = max(0.4, s)
    v = max(0.5, v)
    comp = (h + 0.5) % 1.0
    anchors = [h, (comp - 1 / 12) % 1.0, (comp + 1 / 12) % 1.0]
    results = []
    per_anchor = max(1, count // 3)
    extra = count - per_anchor * 3
    for i, anchor_h in enumerate(anchors):
        slots = per_anchor + (1 if i < extra else 0)
        for j in range(slots):
            v_j = max(0.35, v - 0.15 * j)
            r, g, b = colorsys.hsv_to_rgb(anchor_h, s, v_j)
            results.append(rgb_to_hex(RGB(r, g, b)))
    return results[:count]


def monochromatic(base_hex: str, count: int = 6) -> list[str]:
    """
    Generate a monochromatic palette (same hue, varying saturation and lightness).

    Args:
        base_hex (str): Base color in any supported format.
        count (int): Number of colors to return.

    Returns:
        list[str]: List of hex color strings.
    """
    base = parse_color(base_hex)
    return vary_lightness(base, count)


def random_palette(base_hex: str | None = None, count: int = 6) -> list[str]:
    """
    Generate an aesthetically constrained random palette.

    Uses a randomised analogous spread so the result is coherent rather than fully random.
    The base_hex argument is optional; when omitted a random base hue is chosen.

    Args:
        base_hex (str | None): Optional base color. When None a random hue is used.
        count (int): Number of colors to return.

    Returns:
        list[str]: List of hex color strings.
    """
    if base_hex:
        base = parse_color(base_hex)
        h, s, v = colorsys.rgb_to_hsv(base.r, base.g, base.b)
    else:
        h = random.random()
        s = random.uniform(0.45, 0.85)
        v = random.uniform(0.55, 0.95)

    spread = random.uniform(0.08, 0.25)
    results = []
    for _ in range(count):
        offset = random.uniform(-spread, spread)
        s_var = max(0.25, min(1.0, s + random.uniform(-0.2, 0.2)))
        v_var = max(0.35, min(1.0, v + random.uniform(-0.25, 0.25)))
        r, g, b = colorsys.hsv_to_rgb((h + offset) % 1.0, s_var, v_var)
        results.append(rgb_to_hex(RGB(r, g, b)))
    return results


ALGORITHMS: dict[str, Callable] = {
    "complementary": complementary,
    "analogous": analogous,
    "triadic": triadic,
    "tetradic": tetradic,
    "split_complementary": split_complementary,
    "monochromatic": monochromatic,
    "random": random_palette,
}


def generate(algorithm: str, base_hex: str | None, count: int) -> list[str]:
    """
    Dispatch to the named generation algorithm.

    Args:
        algorithm (str): One of the keys in :data:`ALGORITHMS`.
        base_hex (str | None): Base color string (may be None for the random algorithm).
        count (int): Desired number of colors.

    Returns:
        list[str]: List of hex color strings.

    Raises:
        ValueError: If the algorithm name is unknown.
    """
    if algorithm not in ALGORITHMS:
        raise ValueError(
            f"Unknown algorithm {algorithm!r}. "
            f"Choose from: {', '.join(ALGORITHMS)}"
        )
    fn = ALGORITHMS[algorithm]
    if algorithm == "random":
        colors = fn(base_hex, count)
    else:
        if base_hex is None:
            raise ValueError(f"Algorithm {algorithm!r} requires a base color.")
        colors = fn(base_hex, count)

    # Always pin the first slot to the exact input color so the base is
    # preserved verbatim regardless of any S/V clamping inside the algorithm.
    if base_hex:
        colors[0] = normalise_to_hex(base_hex)

    return colors
