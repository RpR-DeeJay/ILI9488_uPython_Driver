"""
paint_demo.py
=============

Optimized calibrated touch-paint demonstration.

Version: 0.7.1

Two drawing modes are available:

FAST
    Interpolated overlapping square stamps. Each stamp is one
    fill_rect() transfer, making this significantly faster than the
    previous filled-polygon thick line.

SMOOTH
    The earlier rounded thick-line renderer. It looks smoother but uses
    many more display windows and is therefore slower.

Tap MODE at the top-right to compare them. FAST is the default.
Tap EXIT at the top-left to return to the demonstration menu.
"""

from time import sleep_ms

from fast_touch import FastTouchReader

from colour import (
    BLACK,
    WHITE,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    DARK_BLUE,
    DARK_GREY,
    LIGHT_GREY,
)


HEADER_HEIGHT = 34
TOOLBAR_HEIGHT = 40

FAST_BRUSH_SIZE = 7
SMOOTH_BRUSH_SIZE = 8


def _stamp(
    gfx,
    x,
    y,
    size,
    colour,
    minimum_y,
    maximum_y,
):
    """Draw one clipped square brush stamp."""
    half = size // 2

    left = x - half
    top = y - half
    right = left + size
    bottom = top + size

    if top < minimum_y:
        top = minimum_y

    if bottom > maximum_y:
        bottom = maximum_y

    if left < 0:
        left = 0

    if right > gfx.width:
        right = gfx.width

    width = right - left
    height = bottom - top

    if width > 0 and height > 0:
        gfx.fill_rect(
            left,
            top,
            width,
            height,
            colour,
        )


def _fast_stroke(
    gfx,
    x0,
    y0,
    x1,
    y1,
    size,
    colour,
    minimum_y,
    maximum_y,
):
    """
    Join two sampled points with overlapping square stamps.

    Stamp spacing is half the brush size, so quick stylus movement does
    not leave gaps even when touch samples are several pixels apart.
    """
    delta_x = x1 - x0
    delta_y = y1 - y0

    distance = max(
        abs(delta_x),
        abs(delta_y),
    )

    spacing = max(
        1,
        size // 2,
    )

    steps = max(
        1,
        (distance + spacing - 1) // spacing,
    )

    for step in range(1, steps + 1):
        x = x0 + (
            delta_x * step
        ) // steps

        y = y0 + (
            delta_y * step
        ) // steps

        _stamp(
            gfx,
            x,
            y,
            size,
            colour,
            minimum_y,
            maximum_y,
        )


def _draw_toolbar(
    gfx,
    selected_colour,
):
    toolbar_y = gfx.height - TOOLBAR_HEIGHT
    button_width = gfx.width // 8

    colours = (
        RED,
        GREEN,
        BLUE,
        YELLOW,
        CYAN,
        MAGENTA,
        WHITE,
    )

    for index, colour in enumerate(colours):
        x = index * button_width

        gfx.fill_rect(
            x,
            toolbar_y,
            button_width,
            TOOLBAR_HEIGHT,
            colour,
        )

        border = (
            WHITE
            if colour == selected_colour
            else DARK_GREY
        )

        thickness = (
            3
            if colour == selected_colour
            else 1
        )

        for inset in range(thickness):
            gfx.rect(
                x + inset,
                toolbar_y + inset,
                button_width - (2 * inset),
                TOOLBAR_HEIGHT - (2 * inset),
                border,
            )

    clear_x = 7 * button_width

    gfx.fill_rect(
        clear_x,
        toolbar_y,
        gfx.width - clear_x,
        TOOLBAR_HEIGHT,
        DARK_GREY,
    )

    gfx.text(
        "CLR",
        clear_x + 7,
        toolbar_y + 16,
        WHITE,
    )

    return (
        toolbar_y,
        button_width,
        colours,
    )


def _draw_header(
    gfx,
    mode,
):
    gfx.fill_rect(
        0,
        0,
        gfx.width,
        HEADER_HEIGHT,
        DARK_BLUE,
    )

    gfx.text(
        "EXIT",
        8,
        13,
        YELLOW,
        background=DARK_BLUE,
    )

    gfx.text(
        "TOUCH PAINT",
        100,
        13,
        WHITE,
        background=DARK_BLUE,
    )

    mode_text = (
        "FAST"
        if mode == "fast"
        else "SMOOTH"
    )

    gfx.text(
        mode_text,
        gfx.width - gfx.text_width(mode_text) - 8,
        13,
        CYAN,
        background=DARK_BLUE,
    )

    gfx.hline(
        0,
        HEADER_HEIGHT - 1,
        gfx.width,
        CYAN,
    )


def _draw_screen(
    gfx,
    selected_colour,
    mode,
):
    gfx.fill(BLACK)

    _draw_header(
        gfx,
        mode,
    )

    return _draw_toolbar(
        gfx,
        selected_colour,
    )


def run(
    gfx,
    lcd,
    touch,
):
    """
    Run paint until EXIT is touched.
    """
    reader = FastTouchReader(touch)

    selected_colour = CYAN
    mode = "fast"

    (
        toolbar_y,
        button_width,
        colours,
    ) = _draw_screen(
        gfx,
        selected_colour,
        mode,
    )

    previous_x = None
    previous_y = None
    was_touched = False

    print("")
    print("Optimized touch paint")
    print("FAST mode uses interpolated fill_rect stamps")
    print("Tap MODE to compare SMOOTH mode")

    while True:
        point = reader.read()

        if point is None:
            previous_x = None
            previous_y = None
            was_touched = False
            sleep_ms(1)
            continue

        x, y = point

        if y < HEADER_HEIGHT:
            if not was_touched:
                if x < 62:
                    touch.wait_for_release()
                    return

                if x > gfx.width - 80:
                    mode = (
                        "smooth"
                        if mode == "fast"
                        else "fast"
                    )

                    _draw_header(
                        gfx,
                        mode,
                    )

            previous_x = None
            previous_y = None
            was_touched = True
            sleep_ms(2)
            continue

        if y >= toolbar_y:
            if not was_touched:
                button_index = min(
                    7,
                    x // button_width,
                )

                if button_index == 7:
                    (
                        toolbar_y,
                        button_width,
                        colours,
                    ) = _draw_screen(
                        gfx,
                        selected_colour,
                        mode,
                    )
                else:
                    selected_colour = colours[
                        button_index
                    ]

                    _draw_toolbar(
                        gfx,
                        selected_colour,
                    )

            previous_x = None
            previous_y = None
            was_touched = True
            sleep_ms(2)
            continue

        if previous_x is None:
            if mode == "fast":
                _stamp(
                    gfx,
                    x,
                    y,
                    FAST_BRUSH_SIZE,
                    selected_colour,
                    HEADER_HEIGHT,
                    toolbar_y,
                )
            else:
                gfx.fill_circle(
                    x,
                    y,
                    SMOOTH_BRUSH_SIZE // 2,
                    selected_colour,
                )

        elif mode == "fast":
            _fast_stroke(
                gfx,
                previous_x,
                previous_y,
                x,
                y,
                FAST_BRUSH_SIZE,
                selected_colour,
                HEADER_HEIGHT,
                toolbar_y,
            )

        else:
            gfx.thick_line(
                previous_x,
                previous_y,
                x,
                y,
                SMOOTH_BRUSH_SIZE,
                selected_colour,
                round_caps=True,
            )

        previous_x = x
        previous_y = y
        was_touched = True

        sleep_ms(1)
