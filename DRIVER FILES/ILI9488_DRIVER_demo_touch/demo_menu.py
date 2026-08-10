"""
demo_menu.py
============

Touch-driven demonstration menu.

Version: 0.7.1
"""

import gc
import sys

from colour import (
    BLACK,
    WHITE,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    ORANGE,
    PURPLE,
    DARK_BLUE,
    DARK_GREEN,
    DARK_GREY,
    LIGHT_GREY,
)

from layout import text_box

from demo_runner import (
    run_module,
    run_all,
)


BUTTONS = (
    ("BASIC SHAPES", "demo_primitives", BLUE),
    ("TEXT", "demo_text", DARK_GREEN),
    ("ADVANCED", "demo_advanced", PURPLE),
    ("IMAGES + SPRITES", "demo_media", ORANGE),
    ("RUN ALL", "__all__", CYAN),
    ("FAST PAINT", "__paint__", MAGENTA),
    ("RECALIBRATE", "__calibrate__", YELLOW),
    ("ABOUT", "__about__", DARK_GREY),
)


def _centred_x(gfx, text, scale=1):
    width = gfx.text_width(
        text,
        scale=scale,
    )

    return max(
        0,
        (gfx.width - width) // 2,
    )


def _draw_button(
    gfx,
    index,
    title,
    colour,
):
    columns = 2
    rows = 4

    margin_x = 10
    gap_x = 8
    gap_y = 10

    top = 92
    bottom = gfx.height - 18

    button_width = (
        gfx.width
        - (margin_x * 2)
        - gap_x
    ) // columns

    button_height = (
        bottom
        - top
        - (gap_y * (rows - 1))
    ) // rows

    column = index % columns
    row = index // columns

    x = (
        margin_x
        + column * (
            button_width + gap_x
        )
    )

    y = (
        top
        + row * (
            button_height + gap_y
        )
    )

    gfx.fill_round_rect(
        x,
        y,
        button_width,
        button_height,
        10,
        colour,
    )

    gfx.round_rect(
        x,
        y,
        button_width,
        button_height,
        10,
        WHITE,
    )

    text_box(
        gfx,
        title,
        x + 6,
        y + 8,
        button_width - 12,
        button_height - 16,
        BLACK,
        line_spacing=2,
        align="centre",
    )

    return (
        x,
        y,
        button_width,
        button_height,
    )


def draw_menu(gfx):
    """Draw the main touch menu and return button rectangles."""
    gfx.gradient_rect(
        0,
        0,
        gfx.width,
        gfx.height,
        DARK_BLUE,
        BLACK,
        vertical=True,
    )

    gfx.text(
        "ILI9488 DRIVER",
        _centred_x(
            gfx,
            "ILI9488 DRIVER",
            scale=2,
        ),
        18,
        WHITE,
        background=DARK_BLUE,
        scale=2,
    )

    gfx.text(
        "VERSION 0.7.1 - TOUCH EDITION",
        _centred_x(
            gfx,
            "VERSION 0.7.1 - TOUCH EDITION",
        ),
        56,
        CYAN,
    )

    rectangles = []

    for index, item in enumerate(BUTTONS):
        title, action, colour = item

        rectangle = _draw_button(
            gfx,
            index,
            title,
            colour,
        )

        rectangles.append(
            (
                rectangle,
                action,
            )
        )

    return rectangles


def _wait_selection(
    touch,
    rectangles,
):
    """Wait for one released-then-pressed menu selection."""
    touch.wait_for_release()

    while True:
        point = touch.read(samples=3)

        if point is None:
            continue

        x, y, _ = point

        for rectangle, action in rectangles:
            button_x, button_y, width, height = rectangle

            if (
                button_x <= x < button_x + width
                and button_y <= y < button_y + height
            ):
                touch.wait_for_release()
                return action


def _about(gfx, touch):
    gfx.fill(BLACK)

    gfx.text(
        "VERSION 0.7.1",
        _centred_x(
            gfx,
            "VERSION 0.7.1",
            scale=2,
        ),
        34,
        CYAN,
        scale=2,
    )

    text_box(
        gfx,
        "This edition retains the complete shape, text, gradient, BMP, "
        "RAW and sprite demonstrations. It also adds a touch menu and "
        "a faster paint path using three-sample X/Y polling and "
        "interpolated rectangle stamps.",
        20,
        95,
        gfx.width - 40,
        215,
        WHITE,
        line_spacing=3,
        align="centre",
    )

    text_box(
        gfx,
        "FAST paint prioritizes response and continuity. SMOOTH paint "
        "uses rounded thick lines and remains available for comparison.",
        20,
        330,
        gfx.width - 40,
        75,
        YELLOW,
        line_spacing=2,
        align="centre",
    )

    text_box(
        gfx,
        "Touch anywhere to return.",
        20,
        430,
        gfx.width - 40,
        30,
        GREEN,
        align="centre",
    )

    touch.wait_for_release()
    touch.wait_for_touch()
    touch.wait_for_release()


def _run_paint(
    gfx,
    lcd,
    touch,
):
    module_name = "paint_demo"
    module = __import__(module_name)

    try:
        module.run(
            gfx,
            lcd,
            touch,
        )
    finally:
        del module

        try:
            del sys.modules[module_name]
        except KeyError:
            pass

        gc.collect()


def loop(
    gfx,
    lcd,
    touch,
    touch_class,
    rotation,
    calibration_file,
):
    """Run the touch menu indefinitely."""
    while True:
        rectangles = draw_menu(gfx)
        action = _wait_selection(
            touch,
            rectangles,
        )

        if action == "__all__":
            run_all(
                gfx,
                lcd,
                touch=touch,
                auto=True,
            )

        elif action == "__paint__":
            _run_paint(
                gfx,
                lcd,
                touch,
            )

        elif action == "__calibrate__":
            calibration_module = __import__(
                "calibration_ui"
            )

            try:
                calibration_module.calibrate(
                    gfx,
                    touch,
                    touch_class,
                    rotation,
                    calibration_file=calibration_file,
                )
            finally:
                del calibration_module
                gc.collect()

        elif action == "__about__":
            _about(
                gfx,
                touch,
            )

        else:
            run_module(
                action,
                gfx,
                lcd,
                touch=touch,
                auto=False,
            )
