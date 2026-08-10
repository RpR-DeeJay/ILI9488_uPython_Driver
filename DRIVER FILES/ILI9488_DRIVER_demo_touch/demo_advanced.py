"""
demo_advanced.py
================

Advanced shape and gradient demonstrations retained from Version 0.4.

Version: 0.7.1
"""

from colour import (
    BLACK,
    WHITE,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    ORANGE,
    PURPLE,
    DARK_BLUE,
    DARK_GREEN,
    LIGHT_GREY,
)

from demo_common import (
    page_header,
    footer,
)


def _ellipses_and_rounded(gfx, touch, auto):
    page_header(
        gfx,
        "ELLIPSES AND ROUNDED BOXES",
        "Filled ellipses and gradients clipped to rounded rectangles.",
    )

    gfx.fill_ellipse(
        80,
        180,
        58,
        30,
        BLUE,
    )
    gfx.ellipse(
        80,
        180,
        58,
        30,
        CYAN,
    )

    gfx.fill_ellipse(
        238,
        180,
        30,
        58,
        DARK_GREEN,
    )
    gfx.ellipse(
        238,
        180,
        30,
        58,
        GREEN,
    )

    gfx.gradient_round_rect(
        28,
        285,
        264,
        88,
        22,
        RED,
        YELLOW,
        vertical=False,
    )

    gfx.round_rect(
        28,
        285,
        264,
        88,
        22,
        WHITE,
    )

    gfx.text(
        "ROUNDED GRADIENT",
        70,
        326,
        BLACK,
    )

    footer(
        gfx,
        touch=touch,
        auto=auto,
    )


def _polygons_arcs_and_thick_lines(gfx, touch, auto):
    page_header(
        gfx,
        "POLYGONS, ARCS AND STROKES",
        "Arbitrary polygons, regular polygons, arcs and thick line bodies.",
    )

    points = (
        (22, 190),
        (90, 125),
        (138, 195),
        (112, 265),
        (38, 255),
    )

    gfx.fill_polygon(
        points,
        BLUE,
    )
    gfx.polygon(
        points,
        WHITE,
    )

    gfx.regular_polygon(
        235,
        192,
        64,
        7,
        YELLOW,
        rotation=270,
        fill=True,
    )
    gfx.regular_polygon(
        235,
        192,
        64,
        7,
        WHITE,
        rotation=270,
        fill=False,
    )

    gfx.arc(
        80,
        355,
        55,
        195,
        525,
        CYAN,
        thickness=5,
        step=4,
    )

    gfx.thick_line(
        150,
        325,
        292,
        395,
        13,
        MAGENTA,
        round_caps=True,
    )

    footer(
        gfx,
        touch=touch,
        auto=auto,
    )


def run(gfx, lcd, touch=None, auto=False):
    """Run all advanced graphics demonstrations."""
    _ellipses_and_rounded(
        gfx,
        touch,
        auto,
    )

    _polygons_arcs_and_thick_lines(
        gfx,
        touch,
        auto,
    )
