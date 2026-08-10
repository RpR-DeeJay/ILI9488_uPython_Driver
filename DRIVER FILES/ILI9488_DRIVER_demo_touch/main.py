"""
main.py
=======

ILI9488 MicroPython Driver Version 0.7.1 - Touch Edition.

This boot-safe launcher initializes the LCD before importing the larger
graphics, calibration, menu and demonstration modules.

Touch features
--------------
- XPT2046-compatible shared-SPI input
- automatic saved four-point calibration detection
- complete retained display demonstration menu
- optimized FAST paint mode
- optional SMOOTH paint mode

Important wiring
----------------
LCD SDO must remain disconnected when Touch T_DO uses X7.

    Touch T_CLK -> X6
    Touch T_CS  -> X2
    Touch T_DIN -> X8
    Touch T_DO  -> X7
    Touch T_IRQ -> X1
"""

import gc
import sys

from pyb import Pin, SPI

from display import Display

from colour import (
    BLACK,
    WHITE,
    RED,
    YELLOW,
    CYAN,
    DARK_BLUE,
    LIGHT_GREY,
)


DISPLAY_BAUDRATE = 10_000_000
TOUCH_BAUDRATE = 1_000_000

ROTATION = 0

CALIBRATION_FILE = "touch_calibration.py"

LCD = None
GFX = None
TOUCH = None


def free_heap():
    gc.collect()

    try:
        return gc.mem_free()
    except AttributeError:
        return -1


def initialize_display():
    """Initialize the display before importing larger modules."""
    lcd_cs = Pin("X5", Pin.OUT_PP)
    lcd_dc = Pin("X4", Pin.OUT_PP)
    lcd_rst = Pin("X3", Pin.OUT_PP)

    touch_cs = Pin("X2", Pin.OUT_PP)
    touch_irq = Pin(
        "X1",
        Pin.IN,
        Pin.PULL_UP,
    )

    lcd_cs.value(1)
    lcd_dc.value(1)
    lcd_rst.value(1)
    touch_cs.value(1)

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
        buffer_pixels=144,
    )

    lcd.begin()
    lcd.fill(DARK_BLUE)

    return (
        lcd,
        spi,
        lcd_cs,
        touch_cs,
        touch_irq,
    )


def show_error(error):
    """Show a startup/runtime error on serial and the initialized LCD."""
    print("")
    print("Version 0.7.1 Touch Edition stopped:")

    try:
        sys.print_exception(error)
    except AttributeError:
        print(repr(error))

    if GFX is None:
        return

    try:
        GFX.fill(BLACK)

        GFX.text(
            "DRIVER ERROR",
            60,
            28,
            RED,
            scale=2,
        )

        GFX.text(
            type(error).__name__,
            12,
            86,
            YELLOW,
        )

        message = str(error)

        if not message:
            message = "See serial console."

        start = 0
        line_y = 125

        while start < len(message) and line_y < 385:
            GFX.text(
                message[start:start + 32],
                12,
                line_y,
                WHITE,
            )

            start += 32
            line_y += 14

        heap = free_heap()

        if heap >= 0:
            GFX.text(
                "FREE HEAP: {}".format(heap),
                12,
                405,
                CYAN,
            )

        GFX.text(
            "SEE SERIAL TRACEBACK",
            12,
            442,
            LIGHT_GREY,
        )

    except Exception as display_error:
        print(
            "Could not draw error:",
            display_error,
        )


def main():
    global LCD
    global GFX
    global TOUCH

    print("")
    print("ILI9488 Driver Version 0.7.1")
    print("Touch Edition")
    print("-----------------------------")
    print("Heap at start:", free_heap())

    (
        LCD,
        spi,
        lcd_cs,
        touch_cs,
        touch_irq,
    ) = initialize_display()

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
        "Heap after display and graphics:",
        free_heap(),
    )

    from touch import Touch

    TOUCH = Touch(
        spi=spi,
        cs=touch_cs,
        irq=touch_irq,
        display_cs=lcd_cs,
        display_baudrate=DISPLAY_BAUDRATE,
        touch_baudrate=TOUCH_BAUDRATE,
        pressure_threshold=80,
        width=LCD.width,
        height=LCD.height,
        debug=False,
    )

    GFX.text(
        "TOUCH DRIVER READY",
        8,
        34,
        CYAN,
        background=DARK_BLUE,
    )

    from calibration_ui import (
        calibration_file_exists,
        load_saved,
        calibrate,
    )

    calibration_present = calibration_file_exists(
        CALIBRATION_FILE
    )

    print(
        "Calibration file present:",
        calibration_present
    )

    calibration_loaded = False

    if calibration_present:
        calibration_loaded = load_saved(
            TOUCH,
            LCD.width,
            LCD.height,
            ROTATION,
            calibration_file=CALIBRATION_FILE,
        )

    if not calibration_loaded:
        calibrate(
            GFX,
            TOUCH,
            Touch,
            ROTATION,
            calibration_file=CALIBRATION_FILE,
        )

    print(
        "Heap before menu:",
        free_heap(),
    )

    from demo_menu import loop

    loop(
        GFX,
        LCD,
        TOUCH,
        Touch,
        ROTATION,
        CALIBRATION_FILE,
    )


try:
    main()

except Exception as error:
    show_error(error)
