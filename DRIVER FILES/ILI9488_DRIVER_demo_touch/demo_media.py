"""
demo_media.py
=============

Low-memory BMP, RAW and sprite demonstrations retained from Version 0.5.

Version: 0.7.1
"""

import gc

from colour import (
    BLACK,
    WHITE,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    DARK_BLUE,
    DARK_GREY,
    LIGHT_GREY,
)

from demo_common import (
    page_header,
    footer,
)

from layout import text_box


DEMO_BMP = "assets/demo.bmp"
DEMO_RAW = "assets/demo.raw"
DEMO_WIDTH = 120
DEMO_HEIGHT = 80


def _streamed_images(gfx, lcd, touch, auto):
    from bitmap import (
        draw_bmp,
        draw_raw,
    )

    page_header(
        gfx,
        "BMP AND RAW STREAMING",
        "Images are converted and transferred one visible row at a time.",
    )

    draw_bmp(
        lcd,
        DEMO_BMP,
        20,
        125,
    )

    draw_raw(
        lcd,
        DEMO_RAW,
        DEMO_WIDTH,
        DEMO_HEIGHT,
        180,
        125,
        byteorder="big",
    )

    gfx.rect(
        19,
        124,
        DEMO_WIDTH + 2,
        DEMO_HEIGHT + 2,
        WHITE,
    )
    gfx.rect(
        179,
        124,
        DEMO_WIDTH + 2,
        DEMO_HEIGHT + 2,
        WHITE,
    )

    gfx.text(
        "24-BIT BMP",
        39,
        218,
        CYAN,
    )
    gfx.text(
        "RGB565 RAW",
        195,
        218,
        YELLOW,
    )

    draw_bmp(
        lcd,
        DEMO_BMP,
        36,
        285,
        source_x=25,
        source_y=15,
        width=70,
        height=50,
    )

    draw_raw(
        lcd,
        DEMO_RAW,
        DEMO_WIDTH,
        DEMO_HEIGHT,
        214,
        285,
        source_x=25,
        source_y=15,
        width=70,
        height=50,
        byteorder="big",
    )

    gfx.rect(
        35,
        284,
        72,
        52,
        WHITE,
    )
    gfx.rect(
        213,
        284,
        72,
        52,
        WHITE,
    )

    text_box(
        gfx,
        "Both lower images are cropped directly from their files "
        "without loading either complete picture into RAM.",
        18,
        355,
        gfx.width - 36,
        68,
        LIGHT_GREY,
        line_spacing=2,
        align="centre",
    )

    footer(
        gfx,
        touch=touch,
        auto=auto,
    )


def _make_keyed_sprite():
    from sprite import Sprite
    from graphics import Graphics

    candidate_sizes = (
        56,
        48,
        40,
    )

    last_error = None

    for size in candidate_sizes:
        gc.collect()

        try:
            sprite = Sprite(
                size,
                size,
                background=MAGENTA,
                transparent=MAGENTA,
            )
        except MemoryError as error:
            last_error = error
            continue

        sprite_gfx = Graphics(sprite)
        centre = size // 2
        outer = max(
            10,
            centre - 4,
        )
        inner = max(
            6,
            size // 4,
        )

        sprite_gfx.circle(
            centre,
            centre,
            outer,
            YELLOW,
        )
        sprite_gfx.circle(
            centre,
            centre,
            outer - 1,
            YELLOW,
        )
        sprite_gfx.circle(
            centre,
            centre,
            inner,
            CYAN,
        )
        sprite_gfx.circle(
            centre,
            centre,
            inner - 1,
            CYAN,
        )

        sprite_gfx.text(
            "K",
            centre - 4,
            centre - 4,
            WHITE,
        )

        return sprite, size

    if last_error is not None:
        raise last_error

    raise MemoryError(
        "no demonstration sprite size could be allocated"
    )


def _sprites_and_transparency(gfx, lcd, touch, auto):
    page_header(
        gfx,
        "SPRITES AND COLOUR KEYING",
        "The same small RGB565 sprite is drawn opaque and keyed over a grid.",
    )

    for x in range(0, gfx.width, 16):
        gfx.vline(
            x,
            112,
            gfx.height - 150,
            DARK_GREY,
        )

    for y in range(112, gfx.height - 38, 16):
        gfx.hline(
            0,
            y,
            gfx.width,
            DARK_GREY,
        )

    sprite, size = _make_keyed_sprite()

    left_x = 45
    right_x = gfx.width - size - 45
    sprite_y = 175

    sprite.draw(
        lcd,
        left_x,
        sprite_y,
        use_sprite_transparency=False,
    )

    sprite.draw(
        lcd,
        right_x,
        sprite_y,
        transparent=MAGENTA,
        use_sprite_transparency=False,
    )

    gfx.rect(
        left_x - 2,
        sprite_y - 2,
        size + 4,
        size + 4,
        WHITE,
    )
    gfx.rect(
        right_x - 2,
        sprite_y - 2,
        size + 4,
        size + 4,
        WHITE,
    )

    gfx.text(
        "OPAQUE",
        left_x,
        sprite_y + size + 22,
        MAGENTA,
    )
    gfx.text(
        "KEYED",
        right_x + 4,
        sprite_y + size + 22,
        GREEN,
    )

    # Release the contiguous pixel buffer immediately after transfer.
    del sprite
    gc.collect()

    text_box(
        gfx,
        "The left copy includes its magenta background. The right copy "
        "skips magenta, so grid lines remain visible through its centre "
        "and corners.",
        18,
        320,
        gfx.width - 36,
        88,
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
    """Run all image and sprite demonstrations."""
    _streamed_images(
        gfx,
        lcd,
        touch,
        auto,
    )

    _sprites_and_transparency(
        gfx,
        lcd,
        touch,
        auto,
    )
