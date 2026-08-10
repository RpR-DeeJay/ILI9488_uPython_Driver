"""
main.py
=======

ILI9488 MicroPython Driver Version 0.7.0 - Display-Only Edition.

This edition contains the complete display, graphics, text, image and
sprite driver without importing or requiring touchscreen functionality.

No touch pins need to be connected. LCD SDO remains optional because
the display driver performs write-only operation.

The retained demonstration suite runs automatically and finishes on a
capability summary screen.
"""

import gc
import sys

from pyb import Pin, SPI

from display import Display

from colour import (
    BLACK,
    WHITE,
    RED,
    GREEN,
    YELLOW,
    CYAN,
    DARK_BLUE,
    LIGHT_GREY,
)


DISPLAY_BAUDRATE = 10_000_000
ROTATION = 0

LCD = None
GFX = None


def free_heap():
    gc.collect()

    try:
        return gc.mem_free()
    except AttributeError:
        return -1


def initialize_display():
    """Initialize the write-only ILI9488 display."""
    lcd_cs = Pin("X5", Pin.OUT_PP)
    lcd_dc = Pin("X4", Pin.OUT_PP)
    lcd_rst = Pin("X3", Pin.OUT_PP)

    lcd_cs.value(1)
    lcd_dc.value(1)
    lcd_rst.value(1)

    spi = SPI(
        1,
        SPI.MASTER,
        baudrate=DISPLAY_BAUDRATE,
        polarity=0,
        phase=0,
        firstbit=SPI.MSB,
    )

    lcd = Display(
        spi=spi,
        cs=lcd_cs,
        dc=lcd_dc,
        rst=lcd_rst,
        width=320,
        height=480,
        rotation=ROTATION,
        debug=True,
        buffer_pixels=160,
    )

    lcd.begin()
    lcd.fill(DARK_BLUE)

    return lcd


def final_screen(gfx):
    """Leave a summary screen visible after all demonstrations."""
    from layout import text_box

    gfx.gradient_rect(
        0,
        0,
        gfx.width,
        gfx.height,
        DARK_BLUE,
        BLACK,
        vertical=True,
    )

    gfx.round_rect(
        5,
        5,
        gfx.width - 10,
        gfx.height - 10,
        18,
        CYAN,
    )

    gfx.text(
        "ILI9488 DRIVER",
        32,
        25,
        WHITE,
        background=DARK_BLUE,
        scale=2,
    )

    gfx.text(
        "VERSION 0.7.0",
        59,
        64,
        YELLOW,
    )

    text_box(
        gfx,
        "DISPLAY-ONLY EDITION\n\n"
        "Lines, rectangles, circles, triangles, ellipses, polygons, "
        "arcs, thick strokes, gradients, printable text, wrapping, "
        "RGB565 sprites, BMP and RAW streaming are ready.",
        25,
        115,
        gfx.width - 50,
        230,
        WHITE,
        line_spacing=4,
        align="centre",
    )

    gfx.text(
        "NO TOUCH HARDWARE REQUIRED",
        48,
        390,
        GREEN,
    )

    heap = free_heap()

    if heap >= 0:
        gfx.text(
            "FREE HEAP: {}".format(heap),
            72,
            425,
            LIGHT_GREY,
        )


def show_error(error):
    print("")
    print("Version 0.7.0 Display-Only Edition stopped:")

    try:
        sys.print_exception(error)
    except AttributeError:
        print(repr(error))

    if GFX is None:
        return

    GFX.fill(BLACK)
    GFX.text(
        "DRIVER ERROR",
        60,
        30,
        RED,
        scale=2,
    )
    GFX.text(
        type(error).__name__,
        12,
        90,
        YELLOW,
    )

    message = str(error)
    start = 0
    y = 130

    while start < len(message) and y < 410:
        GFX.text(
            message[start:start + 32],
            12,
            y,
            WHITE,
        )
        start += 32
        y += 14


def main():
    global LCD
    global GFX

    print("")
    print("ILI9488 Driver Version 0.7.0")
    print("Display-Only Edition")
    print("----------------------------")
    print("Heap at start:", free_heap())

    LCD = initialize_display()

    from graphics import Graphics

    GFX = Graphics(LCD)

    GFX.text(
        "DISPLAY READY",
        8,
        14,
        CYAN,
        background=DARK_BLUE,
    )

    print(
        "Heap before demonstrations:",
        free_heap(),
    )

    from demo_runner import run_all

    run_all(
        GFX,
        LCD,
        touch=None,
        auto=True,
    )

    final_screen(GFX)

    print("Display-only demonstration complete")


try:
    main()

except Exception as error:
    show_error(error)
