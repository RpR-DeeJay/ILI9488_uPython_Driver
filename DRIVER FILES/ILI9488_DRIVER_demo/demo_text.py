"""
demo_text.py
============

Text demonstrations retained from Version 0.3.

Version: 0.7.0
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
    PURPLE,
    DARK_BLUE,
    DARK_GREY,
    LIGHT_GREY,
)

from demo_common import (
    page_header,
    footer,
)

from layout import text_box


def _character_set(gfx, touch, auto):
    page_header(
        gfx,
        "PRINTABLE ASCII",
        "Complete fixed 8 x 8 printable character set, wrapping and measurement.",
    )

    characters = "".join(
        chr(code)
        for code in range(32, 127)
    )

    text_box(
        gfx,
        characters,
        12,
        125,
        gfx.width - 24,
        145,
        WHITE,
        background=DARK_GREY,
        line_spacing=3,
        align="left",
    )

    sample = (
        "Word wrapping now keeps long instructions inside explicit "
        "width and height limits instead of continuing beyond the edge."
    )

    text_box(
        gfx,
        sample,
        18,
        300,
        gfx.width - 36,
        105,
        CYAN,
        line_spacing=3,
        align="centre",
    )

    footer(
        gfx,
        touch=touch,
        auto=auto,
    )


def _scaling_and_transparency(gfx, touch, auto):
    page_header(
        gfx,
        "TEXT STYLES",
        "Integer scaling, solid backgrounds and transparent overlays.",
    )

    for radius in range(110, 15, -15):
        colour = (
            BLUE
            if (radius // 15) & 1
            else CYAN
        )

        gfx.circle(
            gfx.width // 2,
            245,
            radius,
            colour,
        )

    gfx.text(
        "SCALE 1",
        18,
        118,
        WHITE,
        background=DARK_BLUE,
    )

    gfx.text(
        "SCALE 2",
        18,
        150,
        YELLOW,
        background=PURPLE,
        scale=2,
    )

    # This deliberately overlays the circular pattern.
    gfx.text(
        "TRANSPARENT",
        50,
        235,
        GREEN,
        background=None,
        scale=2,
    )

    gfx.text(
        "SOLID BACKGROUND",
        35,
        305,
        WHITE,
        background=RED,
        scale=2,
    )

    text_box(
        gfx,
        "Circle lines remain visible between foreground pixels of the "
        "transparent label. The red label replaces its complete cells.",
        20,
        360,
        gfx.width - 40,
        65,
        LIGHT_GREY,
        line_spacing=2,
        align="centre",
    )

    footer(
        gfx,
        touch=touch,
        auto=auto,
    )


def run(gfx, lcd, touch=None, auto=False):
    """Run all text demonstrations."""
    _character_set(
        gfx,
        touch,
        auto,
    )

    _scaling_and_transparency(
        gfx,
        touch,
        auto,
    )
