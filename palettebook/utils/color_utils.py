"""
Color format conversion utilities for PaletteBook.

Support for parsing and converting between hex, rgb, hsl, hsv, cmyk, and forza (hsb) formats.
"""

import colorsys
import re
from typing import NamedTuple


class RGB(NamedTuple):

    """Normalised RGB triple with components in [0.0, 1.0]."""

    r: float
    g: float
    b: float


def _fmt_forza(value: float) -> str:
    """
    Format a Forza component to 3 decimal places, stripping trailing zeros but keeping at least 2 decimal places.

    Examples::

        _fmt_forza(1.0)    -> '1.00'
        _fmt_forza(0.9383) -> '0.938'
        _fmt_forza(0.5)    -> '0.50'

    Args:
        value (float): Value in [0, 1].

    Returns:
        str: Formatted string.
    """
    s = f"{value:.3f}"  # e.g. '0.938', '1.000'
    dot = s.index(".")
    s = s.rstrip("0")
    # Ensure at least 2 decimal places
    min_len = dot + 3
    if len(s) < min_len:
        s = s.ljust(min_len, "0")
    return s


_HEX3_RE = re.compile(r"^#?([0-9a-fA-F]{3})$")
_HEX6_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")
_RGB_RE = re.compile(
    r"^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
    r"(?:\s*,\s*[\d.]+)?\s*\)$",
    re.IGNORECASE,
)
_HSL_RE = re.compile(
    r"^hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%?\s*,\s*([\d.]+)%?"
    r"(?:\s*,\s*[\d.]+)?\s*\)$",
    re.IGNORECASE,
)
_HSV_RE = re.compile(
    r"^hsv\(\s*([\d.]+)\s*,\s*([\d.]+)%?\s*,\s*([\d.]+)%?\s*\)$",
    re.IGNORECASE,
)
_CMYK_RE = re.compile(
    r"^cmyk\(\s*([\d.]+)%?\s*,\s*([\d.]+)%?\s*,\s*([\d.]+)%?\s*,\s*([\d.]+)%?\s*\)$",
    re.IGNORECASE,
)
# Forza: three unitless decimals in [0, 1], where forza_h = h/360, forza_s = s/100, forza_b = v/100
_FORZA_RE = re.compile(
    r"^forza\(\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\s*\)$",
    re.IGNORECASE,
)


def parse_color(value: str) -> RGB:  # noqa: C901, PLR0911, PLR0912, PLR0914
    """
    Parse any supported color string to a normalised RGB triple.

    Accepted formats:
    - #rrggbb / rrggbb (6-digit hex)
    - #rgb / rgb (3-digit hex shorthand)
    - rgb(r, g, b) where components are 0-255
    - hsl(h, s%, l%) where h is 0-360 and s/l are 0-100
    - hsv(h, s%, v%) where h is 0-360 and s/v are 0-100
    - cmyk(c%, m%, y%, k%) where components are 0-100
    - forza(h, s, b) where all components are normalised decimals in [0, 1]
        (h = hue/360, s = saturation/100, b = brightness/100)

    Args:
        value (str): Input color string (whitespace is stripped).

    Returns:
        RGB: Normalised RGB triple.

    Raises:
        ValueError: If the format is not recognised or values are out of range.
    """
    value = value.strip()

    # 6-digit hex
    m = _HEX6_RE.match(value)
    if m:
        h = m.group(1)
        return RGB(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)

    # 3-digit hex shorthand
    m = _HEX3_RE.match(value)
    if m:
        h = m.group(1)
        return RGB(
            int(h[0] * 2, 16) / 255,
            int(h[1] * 2, 16) / 255,
            int(h[2] * 2, 16) / 255,
        )

    # RGB tuple
    m = _RGB_RE.match(value)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not all(0 <= v <= 255 for v in (r, g, b)):  # noqa: PLR2004, magic value fine here
            raise ValueError(f"RGB components out of range in: {value!r}")
        return RGB(r / 255, g / 255, b / 255)

    # HSL tuple
    m = _HSL_RE.match(value)
    if m:
        h, s, l_ = float(m.group(1)), float(m.group(2)), float(m.group(3))
        # Accept both 0-1 and 0-100 for s/l
        if s > 1:
            s /= 100
        if l_ > 1:
            l_ /= 100
        h_norm = (h % 360) / 360
        r, g, b = colorsys.hls_to_rgb(h_norm, l_, s)
        return RGB(r, g, b)

    # HSV tuple
    m = _HSV_RE.match(value)
    if m:
        h, s, v = float(m.group(1)), float(m.group(2)), float(m.group(3))
        if s > 1:
            s /= 100
        if v > 1:
            v /= 100
        h_norm = (h % 360) / 360
        r, g, b = colorsys.hsv_to_rgb(h_norm, s, v)
        return RGB(r, g, b)

    # CMYK Value
    m = _CMYK_RE.match(value)
    if m:
        c, mg, y, k = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
        # Accept both 0-1 and 0-100
        if c > 1:
            c /= 100
        if mg > 1:
            mg /= 100
        if y > 1:
            y /= 100
        if k > 1:
            k /= 100
        r = (1.0 - c) * (1.0 - k)
        g = (1.0 - mg) * (1.0 - k)
        b = (1.0 - y) * (1.0 - k)
        return RGB(r, g, b)

    # Forza livery colors (hsb normalized as decimals)
    m = _FORZA_RE.match(value)
    if m:
        fh, fs, fb = float(m.group(1)), float(m.group(2)), float(m.group(3))
        r, g, b = colorsys.hsv_to_rgb(fh % 1.0, fs, fb)
        return RGB(r, g, b)

    raise ValueError(f"Unrecognised color format: {value!r}")


def rgb_to_hex(rgb: RGB) -> str:
    """
    Convert a normalised RGB triple to a lowercase 7-char hex string.

    Args:
        rgb (RGB): Normalised RGB triple.

    Returns:
        str: Hex string like #ff5733.
    """
    r = max(0, min(255, round(rgb.r * 255)))
    g = max(0, min(255, round(rgb.g * 255)))
    b = max(0, min(255, round(rgb.b * 255)))
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a hex color string to an integer RGB triple (0-255).

    Args:
        hex_color (str): Any hex string accepted by :func:`parse_color`.

    Returns:
        tuple[int, int, int]: Tuple of (r, g, b) integers in 0-255.
    """
    rgb = parse_color(hex_color)
    return (round(rgb.r * 255), round(rgb.g * 255), round(rgb.b * 255))


def to_all_formats(value: str) -> dict:  # noqa: PLR0914
    """
    Convert any supported color string to all formats at once.

    Args:
        value (str): Input color string in any supported format.

    Returns:
        dict: Dictionary with keys hex, rgb, hsl, hsv, forza.

    Raises:
        ValueError: If the color cannot be parsed.
    """
    rgb = parse_color(value)
    hex_str = rgb_to_hex(rgb)

    r8, g8, b8 = round(rgb.r * 255), round(rgb.g * 255), round(rgb.b * 255)

    # HSL via colorsys (returns h, l, s)
    h_hls, l_, s_hls = colorsys.rgb_to_hls(rgb.r, rgb.g, rgb.b)
    h_deg = round(h_hls * 360)
    s_hsl_pct = round(s_hls * 100)
    l_pct = round(l_ * 100)

    # HSV via colorsys
    h_hsv, s_hsv, v_hsv = colorsys.rgb_to_hsv(rgb.r, rgb.g, rgb.b)
    s_hsv_pct = round(s_hsv * 100)
    v_pct = round(v_hsv * 100)

    return {
        "hex": hex_str,
        "rgb": f"rgb({r8}, {g8}, {b8})",
        "hsl": f"hsl({h_deg}, {s_hsl_pct}%, {l_pct}%)",
        "hsv": f"hsv({h_deg}, {s_hsv_pct}%, {v_pct}%)",
        "forza": f"forza({_fmt_forza(h_hsv)}, {_fmt_forza(s_hsv)}, {_fmt_forza(v_hsv)})",
    }


def normalise_to_hex(value: str) -> str:
    """
    Parse any supported color string and return a canonical hex string.

    Args:
        value (str): Input color string.

    Returns:
        str: Lowercase 7-character hex string like #ff5733.

    Raises:
        ValueError: If the color cannot be parsed.
    """
    return rgb_to_hex(parse_color(value))
