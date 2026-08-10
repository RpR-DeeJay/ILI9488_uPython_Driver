"""
calibration_ui.py
=================

Four-point touchscreen calibration user interface.

Version: 0.7.1

Imported only after the LCD and graphics layer are operational, avoiding
a white-screen failure if later modules encounter a memory problem.
"""

from time import sleep_ms
import os
import sys

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

from layout import text_box
from calibration_math import (
    diagnostics,
    calculate_best,
)


def _centred_x(gfx, text, scale=1):
    width = gfx.text_width(
        text,
        scale=scale
    )

    return max(
        0,
        (gfx.width - width) // 2
    )


def calibration_file_exists(
    calibration_file="touch_calibration.py"
):
    """
    Return True when a saved calibration file exists.

    File presence controls normal startup behavior:

    - present: attempt to load and validate it
    - absent: run calibration automatically
    """
    try:
        os.stat(calibration_file)
        return True
    except OSError:
        return False


def _module_name_from_file(calibration_file):
    """
    Convert a root-level Python filename into its import module name.
    """
    module_name = str(calibration_file)

    if module_name.endswith(".py"):
        module_name = module_name[:-3]

    module_name = module_name.rsplit("/", 1)[-1]
    module_name = module_name.rsplit("\\", 1)[-1]

    if not module_name:
        raise ValueError("invalid calibration filename")

    return module_name


def load_saved(
    touch,
    width,
    height,
    rotation,
    calibration_file="touch_calibration.py"
):
    """
    Load and validate a saved calibration file.

    Returns False when the file is absent, invalid, or belongs to a
    different display size/rotation. The caller then runs calibration.
    """
    if not calibration_file_exists(calibration_file):
        print(
            "No saved calibration file:",
            calibration_file
        )
        return False

    module_name = _module_name_from_file(
        calibration_file
    )

    try:
        del sys.modules[module_name]
    except KeyError:
        pass

    try:
        saved = __import__(module_name)
    except (ImportError, SyntaxError) as error:
        print(
            "Could not import saved calibration:",
            error
        )
        return False

    calibration = getattr(
        saved,
        "CALIBRATION",
        None
    )

    if (
        calibration is None
        or getattr(saved, "WIDTH", None) != width
        or getattr(saved, "HEIGHT", None) != height
        or getattr(saved, "ROTATION", None) != rotation
    ):
        print(
            "Saved calibration is invalid or does not match "
            "the current display orientation"
        )
        return False

    try:
        touch.set_calibration(
            calibration,
            width=width,
            height=height
        )
    except (TypeError, ValueError) as error:
        print(
            "Saved calibration data was rejected:",
            error
        )
        return False

    print(
        "Loaded calibration from",
        calibration_file,
        ":",
        calibration
    )

    return True


def _draw_target(
    gfx,
    target_x,
    target_y,
    index,
    total,
    previous_raw
):
    gfx.fill(BLACK)

    gfx.fill_rect(
        0,
        0,
        gfx.width,
        48,
        DARK_BLUE
    )

    gfx.text(
        "TOUCH CALIBRATION",
        _centred_x(
            gfx,
            "TOUCH CALIBRATION",
            scale=2
        ),
        13,
        WHITE,
        background=DARK_BLUE,
        scale=2
    )

    point_text = "POINT {} OF {}".format(
        index,
        total
    )

    gfx.text(
        point_text,
        _centred_x(gfx, point_text),
        62,
        YELLOW
    )

    text_box(
        gfx,
        "Touch and hold the centre until the target turns green, "
        "then release your finger.",
        18,
        86,
        gfx.width - 36,
        55,
        LIGHT_GREY,
        line_spacing=2,
        align="centre"
    )

    if previous_raw is not None:
        raw_text = "LAST RAW X:{} Y:{}".format(
            previous_raw[0],
            previous_raw[1]
        )

        gfx.text(
            raw_text,
            _centred_x(gfx, raw_text),
            146,
            CYAN
        )

    gfx.circle(
        target_x,
        target_y,
        20,
        CYAN
    )

    gfx.circle(
        target_x,
        target_y,
        9,
        WHITE
    )

    gfx.hline(
        target_x - 30,
        target_y,
        61,
        RED
    )

    gfx.vline(
        target_x,
        target_y - 30,
        61,
        RED
    )

    gfx.fill_circle(
        target_x,
        target_y,
        3,
        YELLOW
    )

    text_box(
        gfx,
        "T_IRQ only detects a press. Coordinates require T_DO to X7 "
        "and T_DIN to X8.",
        18,
        gfx.height - 58,
        gfx.width - 36,
        46,
        LIGHT_GREY,
        line_spacing=2,
        align="centre"
    )


def _capture_point(
    gfx,
    touch,
    screen_point,
    index,
    total,
    previous_raw
):
    target_x, target_y = screen_point

    while True:
        touch.wait_for_release()

        _draw_target(
            gfx,
            target_x,
            target_y,
            index,
            total,
            previous_raw
        )

        print(
            "Waiting for calibration point",
            index,
            screen_point
        )

        touch.wait_for_touch()
        sleep_ms(100)

        raw = touch.read_raw(
            samples=17,
            require_touch=True
        )

        if raw is None:
            text_box(
                gfx,
                "Reading lost. Release and try this target again.",
                20,
                160,
                gfx.width - 40,
                48,
                RED,
                background=BLACK,
                align="centre"
            )

            touch.wait_for_release()
            sleep_ms(600)
            continue

        raw_x, raw_y, z1 = raw

        gfx.circle(
            target_x,
            target_y,
            22,
            GREEN
        )

        gfx.fill_circle(
            target_x,
            target_y,
            6,
            GREEN
        )

        raw_text = "RAW X:{} Y:{} Z:{}".format(
            raw_x,
            raw_y,
            z1
        )

        gfx.fill_rect(
            6,
            160,
            gfx.width - 12,
            18,
            BLACK
        )

        gfx.text(
            raw_text,
            _centred_x(gfx, raw_text),
            164,
            GREEN
        )

        print(
            "Raw point",
            index,
            raw_x,
            raw_y,
            "Z1",
            z1
        )

        touch.wait_for_release()
        sleep_ms(250)

        return raw_x, raw_y


def _show_failure(
    gfx,
    touch,
    error,
    raw_points
):
    result = diagnostics(raw_points)

    print("Calibration failed:", error)
    print("Raw points:", raw_points)
    print("Diagnostics:", result)

    gfx.fill(BLACK)

    gfx.text(
        "CALIBRATION FAILED",
        _centred_x(
            gfx,
            "CALIBRATION FAILED",
            scale=2
        ),
        24,
        RED,
        scale=2
    )

    text_box(
        gfx,
        str(error),
        16,
        72,
        gfx.width - 32,
        66,
        YELLOW,
        line_spacing=2,
        align="centre"
    )

    range_text = (
        "RAW X: {} TO {}  SPAN {}\n"
        "RAW Y: {} TO {}  SPAN {}"
    ).format(
        result["x_min"],
        result["x_max"],
        result["x_span"],
        result["y_min"],
        result["y_max"],
        result["y_span"]
    )

    text_box(
        gfx,
        range_text,
        18,
        155,
        gfx.width - 36,
        65,
        CYAN,
        line_spacing=3,
        align="centre"
    )

    text_box(
        gfx,
        "The visible touch reaction comes from T_IRQ. If either span "
        "is small, check T_DO to X7 and T_DIN to X8. Also check T_CLK "
        "to X6 and T_CS to X2.",
        16,
        242,
        gfx.width - 32,
        115,
        WHITE,
        line_spacing=2,
        align="centre"
    )

    text_box(
        gfx,
        "Touch anywhere to retry all four points.",
        20,
        398,
        gfx.width - 40,
        44,
        GREEN,
        line_spacing=2,
        align="centre"
    )

    touch.wait_for_release()
    touch.wait_for_touch()
    touch.wait_for_release()
    sleep_ms(250)


def _show_success(
    gfx,
    touch,
    calibration_file
):
    gfx.fill(BLACK)

    gfx.text(
        "CALIBRATION SAVED",
        _centred_x(
            gfx,
            "CALIBRATION SAVED",
            scale=2
        ),
        45,
        GREEN,
        scale=2
    )

    text_box(
        gfx,
        "Touch the centre target to verify the mapped position.",
        20,
        100,
        gfx.width - 40,
        48,
        WHITE,
        line_spacing=2,
        align="centre"
    )

    centre_x = gfx.width // 2
    centre_y = gfx.height // 2

    gfx.circle(
        centre_x,
        centre_y,
        22,
        YELLOW
    )

    gfx.hline(
        centre_x - 30,
        centre_y,
        61,
        RED
    )

    gfx.vline(
        centre_x,
        centre_y - 30,
        61,
        RED
    )

    touch.wait_for_release()
    touch.wait_for_touch()
    point = touch.read(samples=13)
    touch.wait_for_release()

    if point is not None:
        mapped_x, mapped_y, _ = point

        gfx.fill_circle(
            mapped_x,
            mapped_y,
            6,
            GREEN
        )

        result = "X:{} Y:{}  ERROR X:{} Y:{}".format(
            mapped_x,
            mapped_y,
            mapped_x - centre_x,
            mapped_y - centre_y
        )

        text_box(
            gfx,
            result,
            14,
            320,
            gfx.width - 28,
            50,
            CYAN,
            line_spacing=2,
            align="centre"
        )

        print("Centre verification:", result)

    text_box(
        gfx,
        "Saved as " + calibration_file,
        20,
        404,
        gfx.width - 40,
        40,
        LIGHT_GREY,
        align="centre"
    )

    sleep_ms(1500)


def calibrate(
    gfx,
    touch,
    touch_class,
    rotation,
    calibration_file="touch_calibration.py"
):
    """Run a retrying four-point calibration."""
    margin_x = 42
    top_y = 190
    bottom_y = gfx.height - 105

    screen_points = (
        (margin_x, top_y),
        (gfx.width - margin_x - 1, top_y),
        (
            gfx.width - margin_x - 1,
            bottom_y
        ),
        (margin_x, bottom_y)
    )

    while True:
        raw_points = []
        previous_raw = None

        for index, point in enumerate(
            screen_points,
            start=1
        ):
            captured = _capture_point(
                gfx,
                touch,
                point,
                index,
                len(screen_points),
                previous_raw
            )

            raw_points.append(captured)
            previous_raw = captured

        try:
            calibration, selected, result = calculate_best(
                touch_class,
                raw_points,
                screen_points,
                minimum_axis_span=120,
                minimum_determinant=10000
            )

        except ValueError as error:
            _show_failure(
                gfx,
                touch,
                error,
                raw_points
            )
            continue

        touch.set_calibration(
            calibration,
            width=gfx.width,
            height=gfx.height
        )

        touch.save_calibration(
            calibration_file,
            rotation=rotation
        )

        print("Calibration:", calibration)
        print("Selected points:", selected)
        print("Diagnostics:", result)

        _show_success(
            gfx,
            touch,
            calibration_file
        )

        return calibration
