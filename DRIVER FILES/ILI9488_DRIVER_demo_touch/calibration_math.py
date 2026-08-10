"""
calibration_math.py
===================

Compact robust calibration-selection helpers.

Version: 0.7.1

The physical touch driver remains the proven-size Version 0.6.0 driver.
These additional calculations are imported only after the display has
already initialized.
"""


def diagnostics(raw_points):
    """Return raw coordinate ranges and spans."""
    if not raw_points:
        return {
            "point_count": 0,
            "x_min": 0,
            "x_max": 0,
            "x_span": 0,
            "y_min": 0,
            "y_max": 0,
            "y_span": 0,
        }

    x_values = [
        int(point[0])
        for point in raw_points
    ]

    y_values = [
        int(point[1])
        for point in raw_points
    ]

    x_minimum = min(x_values)
    x_maximum = max(x_values)
    y_minimum = min(y_values)
    y_maximum = max(y_values)

    return {
        "point_count": len(raw_points),
        "x_min": x_minimum,
        "x_max": x_maximum,
        "x_span": x_maximum - x_minimum,
        "y_min": y_minimum,
        "y_max": y_maximum,
        "y_span": y_maximum - y_minimum,
    }


def determinant(point0, point1, point2):
    """Return twice the signed area of a raw-coordinate triangle."""
    x0, y0 = point0
    x1, y1 = point1
    x2, y2 = point2

    return (
        x0 * (y1 - y2)
        + x1 * (y2 - y0)
        + x2 * (y0 - y1)
    )


def calculate_best(
    touch_class,
    raw_points,
    screen_points,
    minimum_axis_span=120,
    minimum_determinant=10000
):
    """
    Select the strongest three-point combination.

    Returns:
        (calibration, selected_indices, diagnostics)
    """
    if len(raw_points) != len(screen_points):
        raise ValueError(
            "raw and screen point counts differ"
        )

    if len(raw_points) < 3:
        raise ValueError(
            "at least three calibration points are required"
        )

    result = diagnostics(raw_points)

    if result["x_span"] < int(minimum_axis_span):
        raise ValueError(
            "raw X barely changed; check T_DO to X7 and T_DIN to X8"
        )

    if result["y_span"] < int(minimum_axis_span):
        raise ValueError(
            "raw Y barely changed; check T_DO to X7 and T_DIN to X8"
        )

    best_indices = None
    best_area = 0
    point_count = len(raw_points)

    for first in range(point_count - 2):
        for second in range(first + 1, point_count - 1):
            for third in range(second + 1, point_count):
                area = abs(
                    determinant(
                        raw_points[first],
                        raw_points[second],
                        raw_points[third]
                    )
                )

                if area > best_area:
                    best_area = area
                    best_indices = (
                        first,
                        second,
                        third
                    )

    result["best_determinant"] = best_area

    if (
        best_indices is None
        or best_area < int(minimum_determinant)
    ):
        raise ValueError(
            "raw points do not form a usable two-dimensional area"
        )

    selected_raw = tuple(
        raw_points[index]
        for index in best_indices
    )

    selected_screen = tuple(
        screen_points[index]
        for index in best_indices
    )

    calibration = touch_class.calculate_calibration(
        selected_raw,
        selected_screen
    )

    return calibration, best_indices, result
