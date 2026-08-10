"""
demo_common.py
==============

Shared demonstration-page helpers.

Version: 0.7.0

The same demonstration modules work in both editions:

- Touch edition: touch anywhere to advance.
- Display-only edition: pages advance after a timed delay.
"""

from time import sleep_ms

from colour import (
    BLACK,
    WHITE,
    YELLOW,
    CYAN,
    DARK_BLUE,
    LIGHT_GREY,
)

from layout import text_box


def centred_x(gfx, text, scale=1, spacing=1):
    """Return an x coordinate that centres fixed-font text."""
    width = gfx.text_width(
        text,
        scale=scale,
        spacing=spacing,
    )

    return max(
        0,
        (gfx.width - width) // 2,
    )


def page_header(gfx, title, subtitle=None):
    """Clear the display and draw a consistent demonstration heading."""
    gfx.fill(BLACK)

    gfx.fill_rect(
        0,
        0,
        gfx.width,
        48,
        DARK_BLUE,
    )

    gfx.text(
        title,
        centred_x(gfx, title),
        13,
        WHITE,
        background=DARK_BLUE,
    )

    if subtitle:
        text_box(
            gfx,
            subtitle,
            14,
            58,
            gfx.width - 28,
            50,
            LIGHT_GREY,
            line_spacing=2,
            align="centre",
        )


def footer(
    gfx,
    touch=None,
    auto=False,
    delay_ms=2800,
    text=None,
):
    """
    Draw a footer and wait for touch or a timed delay.
    """
    if text is None:
        text = (
            "Touch anywhere to continue"
            if touch is not None and not auto
            else "Automatic demonstration"
        )

    footer_y = gfx.height - 30

    gfx.fill_rect(
        0,
        footer_y,
        gfx.width,
        30,
        DARK_BLUE,
    )

    gfx.text(
        text,
        centred_x(gfx, text),
        footer_y + 11,
        YELLOW,
        background=DARK_BLUE,
    )

    if touch is None or auto:
        sleep_ms(int(delay_ms))
        return

    touch.wait_for_release()
    touch.wait_for_touch()
    touch.wait_for_release()
    sleep_ms(120)


def information_page(
    gfx,
    title,
    body,
    touch=None,
    auto=False,
    delay_ms=3000,
):
    """Draw a bounded information page."""
    page_header(gfx, title)

    text_box(
        gfx,
        body,
        18,
        78,
        gfx.width - 36,
        gfx.height - 130,
        CYAN,
        line_spacing=3,
        align="centre",
    )

    footer(
        gfx,
        touch=touch,
        auto=auto,
        delay_ms=delay_ms,
    )
