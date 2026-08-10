"""
demo_primitives.py
==================

Basic graphics demonstrations retained from Versions 0.2 and 0.3.

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
    LIGHT_GREY,
)

from demo_common import (
    page_header,
    footer,
)


def _lines_and_rectangles(gfx, touch, auto):
    page_header(
        gfx,
        "LINES AND RECTANGLES",
        "Bresenham lines, filled rectangles, outlines and clipping.",
    )

    centre_x = gfx.width // 2
    centre_y = 225

    for x in range(10, gfx.width, 30):
        gfx.line(
            centre_x,
            centre_y,
            x,
            125,
            CYAN,
        )

        gfx.line(
            centre_x,
            centre_y,
            x,
            330,
            MAGENTA,
        )

    gfx.fill_rect(
        22,
        355,
        82,
        55,
        BLUE,
    )
    gfx.rect(
        22,
        355,
        82,
        55,
        WHITE,
    )

    gfx.fill_rect(
        118,
        355,
        82,
        55,
        GREEN,
    )
    gfx.rect(
        118,
        355,
        82,
        55,
        YELLOW,
    )

    # Deliberately clipped rectangle.
    gfx.fill_rect(
        250,
        365,
        100,
        60,
        RED,
    )
    gfx.rect(
        250,
        365,
        100,
        60,
        WHITE,
    )

    footer(
        gfx,
        touch=touch,
        auto=auto,
    )


def _circles_and_triangles(gfx, touch, auto):
    page_header(
        gfx,
        "CIRCLES AND TRIANGLES",
        "Outlined and filled midpoint circles plus corrected triangle filling.",
    )

    gfx.fill_circle(
        72,
        180,
        46,
        BLUE,
    )
    gfx.circle(
        72,
        180,
        46,
        CYAN,
    )

    gfx.circle(
        245,
        180,
        53,
        YELLOW,
    )
    gfx.circle(
        245,
        180,
        35,
        ORANGE,
    )
    gfx.circle(
        245,
        180,
        18,
        RED,
    )

    gfx.fill_triangle(
        30,
        370,
        105,
        255,
        170,
        370,
        GREEN,
    )
    gfx.triangle(
        30,
        370,
        105,
        255,
        170,
        370,
        WHITE,
    )

    gfx.fill_triangle(
        185,
        270,
        292,
        270,
        238,
        395,
        PURPLE,
    )
    gfx.triangle(
        185,
        270,
        292,
        270,
        238,
        395,
        LIGHT_GREY,
    )

    footer(
        gfx,
        touch=touch,
        auto=auto,
    )


def run(gfx, lcd, touch=None, auto=False):
    """Run the complete basic-primitives demonstration."""
    _lines_and_rectangles(
        gfx,
        touch,
        auto,
    )

    _circles_and_triangles(
        gfx,
        touch,
        auto,
    )
