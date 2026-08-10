"""
graphics.py
===========

Integer-only graphics and text algorithms for the ILI9488 driver.

Version: 0.7.0

Implemented operations
----------------------
- Pixel
- Full-screen fill
- Horizontal and vertical lines
- Bresenham arbitrary lines
- Outlined rectangles
- Filled rectangles
- Outlined circles
- Filled circles
- Outlined triangles
- Filled triangles
- Printable ASCII characters
- Multi-line text
- Integer text scaling
- Transparent or solid text backgrounds
- Tabs, carriage returns and newlines
- Optional automatic line wrapping
- Text measurement
- Ellipses and filled ellipses
- Rounded and filled rounded rectangles
- Outlined and filled polygons
- Regular polygons
- Thick lines with optional round caps
- Clockwise circular arcs
- Horizontal and vertical RGB565 gradients
- Horizontal and vertical rounded-rectangle gradients
- Rendering into compatible off-screen Sprite objects

No floating-point arithmetic or math module is required.
"""

from font8 import (
    FONT_WIDTH,
    FONT_HEIGHT,
    FIRST_CHARACTER,
    LAST_CHARACTER,
    REPLACEMENT_CHARACTER,
    FONT_DATA
)


# Integer sine values from 0 through 90 degrees, scaled by 1024.
# This avoids importing math on the Pyboard while supporting arcs and
# regular polygons.
_SIN_0_TO_90 = (
    0, 18, 36, 54, 71, 89, 107, 125, 143, 160, 178, 195, 213,
    230, 248, 265, 282, 299, 316, 333, 350, 367, 384, 400, 416, 433,
    449, 465, 481, 496, 512, 527, 543, 558, 573, 587, 602, 616, 630,
    644, 658, 672, 685, 698, 711, 724, 737, 749, 761, 773, 784, 796,
    807, 818, 828, 839, 849, 859, 868, 878, 887, 896, 904, 912, 920,
    928, 935, 943, 949, 956, 962, 968, 974, 979, 984, 989, 994, 998,
    1002, 1005, 1008, 1011, 1014, 1016, 1018, 1020, 1022, 1023, 1023, 1024, 1024,
)


class Graphics:
    """
    High-level graphics interface.

    The supplied display object must provide:

        pixel()
        fill()
        fill_rect()
        hline()
        vline()
        width
        height
    """

    def __init__(self, display):
        self.display = display

    @property
    def width(self):
        """Return the active display width."""
        return self.display.width

    @property
    def height(self):
        """Return the active display height."""
        return self.display.height

    def pixel(self, x, y, colour):
        """Draw one pixel."""
        self.display.pixel(x, y, colour)

    def fill(self, colour):
        """Fill the entire display."""
        self.display.fill(colour)

    def hline(self, x, y, length, colour):
        """Draw a horizontal line."""
        self.display.hline(x, y, length, colour)

    def vline(self, x, y, length, colour):
        """Draw a vertical line."""
        self.display.vline(x, y, length, colour)

    def fill_rect(self, x, y, width, height, colour):
        """Draw a filled rectangle."""
        self.display.fill_rect(x, y, width, height, colour)

    def line(self, x0, y0, x1, y1, colour):
        """
        Draw a line using Bresenham's integer line algorithm.
        """
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)

        if y0 == y1:
            start_x = x0 if x0 <= x1 else x1
            self.hline(
                start_x,
                y0,
                abs(x1 - x0) + 1,
                colour
            )
            return

        if x0 == x1:
            start_y = y0 if y0 <= y1 else y1
            self.vline(
                x0,
                start_y,
                abs(y1 - y0) + 1,
                colour
            )
            return

        delta_x = abs(x1 - x0)
        step_x = 1 if x0 < x1 else -1

        delta_y = -abs(y1 - y0)
        step_y = 1 if y0 < y1 else -1

        error = delta_x + delta_y

        while True:
            self.pixel(x0, y0, colour)

            if x0 == x1 and y0 == y1:
                break

            doubled_error = error << 1

            if doubled_error >= delta_y:
                error += delta_y
                x0 += step_x

            if doubled_error <= delta_x:
                error += delta_x
                y0 += step_y

    def rect(self, x, y, width, height, colour):
        """
        Draw an outlined rectangle.

        width and height are the total outside dimensions.
        """
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            return

        if width == 1:
            self.vline(x, y, height, colour)
            return

        if height == 1:
            self.hline(x, y, width, colour)
            return

        self.hline(x, y, width, colour)
        self.hline(
            x,
            y + height - 1,
            width,
            colour
        )

        if height > 2:
            self.vline(
                x,
                y + 1,
                height - 2,
                colour
            )
            self.vline(
                x + width - 1,
                y + 1,
                height - 2,
                colour
            )

    def circle(self, centre_x, centre_y, radius, colour):
        """
        Draw an outlined circle with the midpoint circle algorithm.
        """
        centre_x = int(centre_x)
        centre_y = int(centre_y)
        radius = int(radius)

        if radius < 0:
            return

        if radius == 0:
            self.pixel(centre_x, centre_y, colour)
            return

        x = radius
        y = 0
        error = 1 - radius

        while x >= y:
            self.pixel(centre_x + x, centre_y + y, colour)
            self.pixel(centre_x + y, centre_y + x, colour)
            self.pixel(centre_x - y, centre_y + x, colour)
            self.pixel(centre_x - x, centre_y + y, colour)
            self.pixel(centre_x - x, centre_y - y, colour)
            self.pixel(centre_x - y, centre_y - x, colour)
            self.pixel(centre_x + y, centre_y - x, colour)
            self.pixel(centre_x + x, centre_y - y, colour)

            y += 1

            if error < 0:
                error += (y << 1) + 1
            else:
                x -= 1
                error += ((y - x) << 1) + 1

    def fill_circle(self, centre_x, centre_y, radius, colour):
        """
        Draw a filled circle using horizontal spans.
        """
        centre_x = int(centre_x)
        centre_y = int(centre_y)
        radius = int(radius)

        if radius < 0:
            return

        if radius == 0:
            self.pixel(centre_x, centre_y, colour)
            return

        x = radius
        y = 0
        error = 1 - radius

        while x >= y:
            self.hline(
                centre_x - x,
                centre_y + y,
                (x << 1) + 1,
                colour
            )

            if y != 0:
                self.hline(
                    centre_x - x,
                    centre_y - y,
                    (x << 1) + 1,
                    colour
                )

            if x != y:
                self.hline(
                    centre_x - y,
                    centre_y + x,
                    (y << 1) + 1,
                    colour
                )

                if x != 0:
                    self.hline(
                        centre_x - y,
                        centre_y - x,
                        (y << 1) + 1,
                        colour
                    )

            y += 1

            if error < 0:
                error += (y << 1) + 1
            else:
                x -= 1
                error += ((y - x) << 1) + 1

    def triangle(
        self,
        x0,
        y0,
        x1,
        y1,
        x2,
        y2,
        colour
    ):
        """Draw an outlined triangle."""
        self.line(x0, y0, x1, y1, colour)
        self.line(x1, y1, x2, y2, colour)
        self.line(x2, y2, x0, y0, colour)

    def fill_triangle(
        self,
        x0,
        y0,
        x1,
        y1,
        x2,
        y2,
        colour
    ):
        """
        Draw a filled triangle using integer horizontal scanlines.
        """
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        if y0 > y1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0

        if y1 > y2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1

        if y0 > y1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0

        if y0 == y2:
            minimum_x = min(x0, x1, x2)
            maximum_x = max(x0, x1, x2)

            self.hline(
                minimum_x,
                y0,
                maximum_x - minimum_x + 1,
                colour
            )
            return

        long_height = y2 - y0
        upper_height = y1 - y0
        lower_height = y2 - y1

        for y in range(y0, y2 + 1):
            long_x = x0 + (
                (x2 - x0) * (y - y0)
            ) // long_height

            if y < y1:
                short_x = x0 + (
                    (x1 - x0) * (y - y0)
                ) // upper_height

            elif lower_height == 0:
                short_x = x1

            else:
                short_x = x1 + (
                    (x2 - x1) * (y - y1)
                ) // lower_height

            if long_x > short_x:
                long_x, short_x = short_x, long_x

            self.hline(
                long_x,
                y,
                short_x - long_x + 1,
                colour
            )

    @staticmethod
    def _integer_sqrt(value):
        """
        Return floor(sqrt(value)) using integer arithmetic only.
        """
        value = int(value)

        if value <= 0:
            return 0

        result = 0
        bit = 1

        while bit <= value:
            bit <<= 2

        bit >>= 2

        while bit:
            trial = result + bit

            if value >= trial:
                value -= trial
                result = (result >> 1) + bit
            else:
                result >>= 1

            bit >>= 2

        return result

    @staticmethod
    def _scaled_trig(value, radius):
        """Scale a signed 1024-based trigonometric value."""
        product = int(value) * int(radius)

        if product >= 0:
            return (product + 512) // 1024

        return -((-product + 512) // 1024)

    @staticmethod
    def _sin_cos(angle):
        """
        Return integer sine and cosine values scaled by 1024.

        Screen angles increase clockwise because positive y points down.
        """
        angle = int(angle) % 360

        if angle <= 90:
            sine = _SIN_0_TO_90[angle]
            cosine = _SIN_0_TO_90[90 - angle]

        elif angle <= 180:
            sine = _SIN_0_TO_90[180 - angle]
            cosine = -_SIN_0_TO_90[angle - 90]

        elif angle <= 270:
            sine = -_SIN_0_TO_90[angle - 180]
            cosine = -_SIN_0_TO_90[270 - angle]

        else:
            sine = -_SIN_0_TO_90[360 - angle]
            cosine = _SIN_0_TO_90[angle - 270]

        return sine, cosine

    @staticmethod
    def _rgb565_components(colour):
        """Expand RGB565 into red, green and blue values from 0 to 255."""
        colour = int(colour) & 0xFFFF

        red_5 = (colour >> 11) & 0x1F
        green_6 = (colour >> 5) & 0x3F
        blue_5 = colour & 0x1F

        return (
            (red_5 << 3) | (red_5 >> 2),
            (green_6 << 2) | (green_6 >> 4),
            (blue_5 << 3) | (blue_5 >> 2)
        )

    @staticmethod
    def _components_to_rgb565(red, green, blue):
        """Pack 8-bit RGB components into an RGB565 integer."""
        return (
            ((int(red) & 0xF8) << 8)
            | ((int(green) & 0xFC) << 3)
            | (int(blue) >> 3)
        )

    @staticmethod
    def _normalise_points(points):
        """Convert an iterable of coordinate pairs into integer tuples."""
        normalised = []

        for point in points:
            if len(point) < 2:
                raise ValueError("Each polygon point needs x and y")

            normalised.append((int(point[0]), int(point[1])))

        return normalised

    def ellipse(self, centre_x, centre_y, radius_x, radius_y, colour):
        """
        Draw an outlined ellipse using integer scanline boundary points.
        """
        centre_x = int(centre_x)
        centre_y = int(centre_y)
        radius_x = int(radius_x)
        radius_y = int(radius_y)

        if radius_x < 0 or radius_y < 0:
            return

        if radius_x == 0:
            self.vline(
                centre_x,
                centre_y - radius_y,
                (radius_y << 1) + 1,
                colour
            )
            return

        if radius_y == 0:
            self.hline(
                centre_x - radius_x,
                centre_y,
                (radius_x << 1) + 1,
                colour
            )
            return

        radius_x_squared = radius_x * radius_x
        radius_y_squared = radius_y * radius_y

        previous_left = None
        previous_right = None

        for offset_y in range(-radius_y, radius_y + 1):
            remaining = (
                radius_y_squared
                - (offset_y * offset_y)
            )

            offset_x = self._integer_sqrt(
                (radius_x_squared * remaining)
                // radius_y_squared
            )

            current_y = centre_y + offset_y
            current_left = (
                centre_x - offset_x,
                current_y
            )
            current_right = (
                centre_x + offset_x,
                current_y
            )

            if previous_left is None:
                self.pixel(
                    current_left[0],
                    current_left[1],
                    colour
                )

                if current_right != current_left:
                    self.pixel(
                        current_right[0],
                        current_right[1],
                        colour
                    )
            else:
                self.line(
                    previous_left[0],
                    previous_left[1],
                    current_left[0],
                    current_left[1],
                    colour
                )

                self.line(
                    previous_right[0],
                    previous_right[1],
                    current_right[0],
                    current_right[1],
                    colour
                )

            previous_left = current_left
            previous_right = current_right

    def fill_ellipse(
        self,
        centre_x,
        centre_y,
        radius_x,
        radius_y,
        colour
    ):
        """Draw a filled ellipse with one horizontal span per row."""
        centre_x = int(centre_x)
        centre_y = int(centre_y)
        radius_x = int(radius_x)
        radius_y = int(radius_y)

        if radius_x < 0 or radius_y < 0:
            return

        if radius_x == 0:
            self.vline(
                centre_x,
                centre_y - radius_y,
                (radius_y << 1) + 1,
                colour
            )
            return

        if radius_y == 0:
            self.hline(
                centre_x - radius_x,
                centre_y,
                (radius_x << 1) + 1,
                colour
            )
            return

        radius_x_squared = radius_x * radius_x
        radius_y_squared = radius_y * radius_y

        for offset_y in range(-radius_y, radius_y + 1):
            remaining = (
                radius_y_squared
                - (offset_y * offset_y)
            )

            offset_x = self._integer_sqrt(
                (radius_x_squared * remaining)
                // radius_y_squared
            )

            self.hline(
                centre_x - offset_x,
                centre_y + offset_y,
                (offset_x << 1) + 1,
                colour
            )

    def round_rect(self, x, y, width, height, radius, colour):
        """Draw an outlined rectangle with rounded corners."""
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)
        radius = int(radius)

        if width <= 0 or height <= 0:
            return

        radius = max(0, min(radius, (width - 1) // 2, (height - 1) // 2))

        if radius == 0:
            self.rect(x, y, width, height, colour)
            return

        left_centre = x + radius
        right_centre = x + width - radius - 1
        top_centre = y + radius
        bottom_centre = y + height - radius - 1

        middle_width = width - (radius << 1)
        middle_height = height - (radius << 1)

        if middle_width > 0:
            self.hline(
                left_centre,
                y,
                middle_width,
                colour
            )
            self.hline(
                left_centre,
                y + height - 1,
                middle_width,
                colour
            )

        if middle_height > 0:
            self.vline(
                x,
                top_centre,
                middle_height,
                colour
            )
            self.vline(
                x + width - 1,
                top_centre,
                middle_height,
                colour
            )

        circle_x = radius
        circle_y = 0
        error = 1 - radius

        while circle_x >= circle_y:
            self.pixel(
                left_centre - circle_x,
                top_centre - circle_y,
                colour
            )
            self.pixel(
                left_centre - circle_y,
                top_centre - circle_x,
                colour
            )

            self.pixel(
                right_centre + circle_x,
                top_centre - circle_y,
                colour
            )
            self.pixel(
                right_centre + circle_y,
                top_centre - circle_x,
                colour
            )

            self.pixel(
                left_centre - circle_x,
                bottom_centre + circle_y,
                colour
            )
            self.pixel(
                left_centre - circle_y,
                bottom_centre + circle_x,
                colour
            )

            self.pixel(
                right_centre + circle_x,
                bottom_centre + circle_y,
                colour
            )
            self.pixel(
                right_centre + circle_y,
                bottom_centre + circle_x,
                colour
            )

            circle_y += 1

            if error < 0:
                error += (circle_y << 1) + 1
            else:
                circle_x -= 1
                error += (
                    ((circle_y - circle_x) << 1) + 1
                )

    def fill_round_rect(
        self,
        x,
        y,
        width,
        height,
        radius,
        colour
    ):
        """Draw a filled rectangle with rounded corners."""
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)
        radius = int(radius)

        if width <= 0 or height <= 0:
            return

        radius = max(0, min(radius, (width - 1) // 2, (height - 1) // 2))

        if radius == 0:
            self.fill_rect(x, y, width, height, colour)
            return

        middle_height = height - (radius << 1)

        if middle_height > 0:
            self.fill_rect(
                x,
                y + radius,
                width,
                middle_height,
                colour
            )

        radius_squared = radius * radius
        left_centre = x + radius
        right_centre = x + width - radius - 1

        for row in range(radius):
            vertical_distance = radius - row
            horizontal_distance = self._integer_sqrt(
                radius_squared
                - (vertical_distance * vertical_distance)
            )

            start_x = left_centre - horizontal_distance
            end_x = right_centre + horizontal_distance
            span = end_x - start_x + 1

            self.hline(
                start_x,
                y + row,
                span,
                colour
            )

            self.hline(
                start_x,
                y + height - 1 - row,
                span,
                colour
            )

    def polygon(self, points, colour):
        """Draw the outline of a polygon from coordinate pairs."""
        points = self._normalise_points(points)
        point_count = len(points)

        if point_count == 0:
            return

        if point_count == 1:
            self.pixel(points[0][0], points[0][1], colour)
            return

        for index in range(point_count):
            start = points[index]
            end = points[(index + 1) % point_count]

            self.line(
                start[0],
                start[1],
                end[0],
                end[1],
                colour
            )

    def fill_polygon(self, points, colour):
        """
        Fill a simple polygon with an even-odd scanline algorithm.

        Concave polygons are supported. Self-intersecting polygons use
        the usual even-odd fill rule.
        """
        points = self._normalise_points(points)
        point_count = len(points)

        if point_count < 3:
            self.polygon(points, colour)
            return

        minimum_y = min(point[1] for point in points)
        maximum_y = max(point[1] for point in points)

        intersections = []

        for scan_y in range(minimum_y, maximum_y):
            intersections.clear()

            for index in range(point_count):
                x0, y0 = points[index]
                x1, y1 = points[(index + 1) % point_count]

                if y0 == y1:
                    continue

                if y0 < y1:
                    lower_x = x0
                    lower_y = y0
                    upper_x = x1
                    upper_y = y1
                else:
                    lower_x = x1
                    lower_y = y1
                    upper_x = x0
                    upper_y = y0

                if scan_y < lower_y or scan_y >= upper_y:
                    continue

                intersection_x = lower_x + (
                    (scan_y - lower_y)
                    * (upper_x - lower_x)
                ) // (upper_y - lower_y)

                intersections.append(intersection_x)

            intersections.sort()

            for index in range(0, len(intersections) - 1, 2):
                start_x = intersections[index]
                end_x = intersections[index + 1]

                if end_x < start_x:
                    start_x, end_x = end_x, start_x

                self.hline(
                    start_x,
                    scan_y,
                    end_x - start_x + 1,
                    colour
                )

        # Seal the boundary and include the polygon's maximum-y edge.
        self.polygon(points, colour)

    def regular_polygon(
        self,
        centre_x,
        centre_y,
        radius,
        sides,
        colour,
        rotation=270,
        fill=False
    ):
        """
        Draw an outlined or filled regular polygon.

        Angles increase clockwise. rotation=270 places the first vertex
        at the top of the screen.
        """
        centre_x = int(centre_x)
        centre_y = int(centre_y)
        radius = int(radius)
        sides = int(sides)
        rotation = int(rotation)

        if radius < 0 or sides < 3:
            return

        points = []

        for index in range(sides):
            angle = rotation + ((index * 360) // sides)
            sine, cosine = self._sin_cos(angle)

            points.append((
                centre_x + self._scaled_trig(cosine, radius),
                centre_y + self._scaled_trig(sine, radius)
            ))

        if fill:
            self.fill_polygon(points, colour)
        else:
            self.polygon(points, colour)

    def thick_line(
        self,
        x0,
        y0,
        x1,
        y1,
        thickness,
        colour,
        round_caps=True
    ):
        """
        Draw an approximately specified-width line as a filled polygon.
        """
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)
        thickness = int(thickness)

        if thickness <= 1:
            self.line(x0, y0, x1, y1, colour)
            return

        delta_x = x1 - x0
        delta_y = y1 - y0
        length = self._integer_sqrt(
            (delta_x * delta_x) + (delta_y * delta_y)
        )

        cap_radius = max(1, thickness // 2)

        if length == 0:
            self.fill_circle(x0, y0, cap_radius, colour)
            return

        offset_x = (
            -delta_y * thickness
        ) // (length << 1)
        offset_y = (
            delta_x * thickness
        ) // (length << 1)

        # Very thin diagonal lines can round both offsets to zero.
        if offset_x == 0 and offset_y == 0:
            if abs(delta_x) >= abs(delta_y):
                offset_y = 1 if delta_x >= 0 else -1
            else:
                offset_x = -1 if delta_y >= 0 else 1

        body = (
            (x0 + offset_x, y0 + offset_y),
            (x1 + offset_x, y1 + offset_y),
            (x1 - offset_x, y1 - offset_y),
            (x0 - offset_x, y0 - offset_y)
        )

        self.fill_polygon(body, colour)

        if round_caps:
            self.fill_circle(x0, y0, cap_radius, colour)
            self.fill_circle(x1, y1, cap_radius, colour)

    def arc(
        self,
        centre_x,
        centre_y,
        radius,
        start_angle,
        end_angle,
        colour,
        thickness=1,
        step=1
    ):
        """
        Draw a clockwise circular arc using the integer sine table.

        Zero degrees points right and 90 degrees points down. If the end
        angle is less than the start angle, the arc wraps through zero.
        A span of 360 degrees draws a complete circle.
        """
        centre_x = int(centre_x)
        centre_y = int(centre_y)
        radius = int(radius)
        start_angle = int(start_angle)
        end_angle = int(end_angle)
        thickness = max(1, int(thickness))
        step = max(1, int(step))

        if radius < 0:
            return

        raw_span = end_angle - start_angle

        if abs(raw_span) >= 360:
            span = 360
        elif raw_span < 0:
            span = raw_span % 360
        else:
            span = raw_span

        sine, cosine = self._sin_cos(start_angle)
        first_x = centre_x + self._scaled_trig(cosine, radius)
        first_y = centre_y + self._scaled_trig(sine, radius)

        previous_x = first_x
        previous_y = first_y

        offset = step

        while offset < span:
            sine, cosine = self._sin_cos(start_angle + offset)
            current_x = centre_x + self._scaled_trig(cosine, radius)
            current_y = centre_y + self._scaled_trig(sine, radius)

            if thickness == 1:
                self.line(
                    previous_x,
                    previous_y,
                    current_x,
                    current_y,
                    colour
                )
            else:
                self.thick_line(
                    previous_x,
                    previous_y,
                    current_x,
                    current_y,
                    thickness,
                    colour,
                    round_caps=False
                )

            previous_x = current_x
            previous_y = current_y
            offset += step

        sine, cosine = self._sin_cos(start_angle + span)
        final_x = centre_x + self._scaled_trig(cosine, radius)
        final_y = centre_y + self._scaled_trig(sine, radius)

        if thickness == 1:
            self.line(
                previous_x,
                previous_y,
                final_x,
                final_y,
                colour
            )
        else:
            self.thick_line(
                previous_x,
                previous_y,
                final_x,
                final_y,
                thickness,
                colour,
                round_caps=False
            )

            if span < 360:
                cap_radius = max(1, thickness // 2)
                self.fill_circle(
                    first_x,
                    first_y,
                    cap_radius,
                    colour
                )
                self.fill_circle(
                    final_x,
                    final_y,
                    cap_radius,
                    colour
                )

    def gradient_rect(
        self,
        x,
        y,
        width,
        height,
        start_colour,
        end_colour,
        vertical=True
    ):
        """
        Fill a rectangle with a linear RGB565 colour gradient.

        vertical=True changes colour from top to bottom.
        vertical=False changes colour from left to right.
        """
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            return

        clipped_x0 = max(0, x)
        clipped_y0 = max(0, y)
        clipped_x1 = min(self.width, x + width) - 1
        clipped_y1 = min(self.height, y + height) - 1

        if clipped_x0 > clipped_x1 or clipped_y0 > clipped_y1:
            return

        start_red, start_green, start_blue = (
            self._rgb565_components(start_colour)
        )
        end_red, end_green, end_blue = (
            self._rgb565_components(end_colour)
        )

        if vertical:
            denominator = max(1, height - 1)

            for screen_y in range(clipped_y0, clipped_y1 + 1):
                position = screen_y - y

                red = start_red + (
                    (end_red - start_red) * position
                ) // denominator
                green = start_green + (
                    (end_green - start_green) * position
                ) // denominator
                blue = start_blue + (
                    (end_blue - start_blue) * position
                ) // denominator

                colour = self._components_to_rgb565(
                    red,
                    green,
                    blue
                )

                self.hline(
                    clipped_x0,
                    screen_y,
                    clipped_x1 - clipped_x0 + 1,
                    colour
                )

        else:
            denominator = max(1, width - 1)

            for screen_x in range(clipped_x0, clipped_x1 + 1):
                position = screen_x - x

                red = start_red + (
                    (end_red - start_red) * position
                ) // denominator
                green = start_green + (
                    (end_green - start_green) * position
                ) // denominator
                blue = start_blue + (
                    (end_blue - start_blue) * position
                ) // denominator

                colour = self._components_to_rgb565(
                    red,
                    green,
                    blue
                )

                self.vline(
                    screen_x,
                    clipped_y0,
                    clipped_y1 - clipped_y0 + 1,
                    colour
                )

    def gradient_round_rect(
        self,
        x,
        y,
        width,
        height,
        radius,
        start_colour,
        end_colour,
        vertical=True
    ):
        """
        Fill a rounded rectangle with a linear RGB565 gradient.

        Unlike drawing gradient_rect() followed by round_rect(), this
        method clips every gradient row or column to the rounded shape,
        so no colour is written into the four outside corner areas.

        Parameters
        ----------
        x, y : int
            Top-left coordinate.
        width, height : int
            Total outside dimensions.
        radius : int
            Corner radius. It is automatically limited to fit.
        start_colour, end_colour : int
            RGB565 endpoint colours.
        vertical : bool
            True changes colour from top to bottom.
            False changes colour from left to right.
        """
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)
        radius = int(radius)

        if width <= 0 or height <= 0:
            return

        radius = max(
            0,
            min(
                radius,
                (width - 1) // 2,
                (height - 1) // 2
            )
        )

        if radius == 0:
            self.gradient_rect(
                x,
                y,
                width,
                height,
                start_colour,
                end_colour,
                vertical
            )
            return

        clipped_x0 = max(0, x)
        clipped_y0 = max(0, y)
        clipped_x1 = min(self.width, x + width) - 1
        clipped_y1 = min(self.height, y + height) - 1

        if clipped_x0 > clipped_x1 or clipped_y0 > clipped_y1:
            return

        start_red, start_green, start_blue = (
            self._rgb565_components(start_colour)
        )
        end_red, end_green, end_blue = (
            self._rgb565_components(end_colour)
        )

        radius_squared = radius * radius

        if vertical:
            denominator = max(1, height - 1)

            for screen_y in range(clipped_y0, clipped_y1 + 1):
                local_y = screen_y - y
                edge_distance = min(
                    local_y,
                    height - 1 - local_y
                )

                if edge_distance < radius:
                    circle_distance = radius - edge_distance
                    corner_extent = self._integer_sqrt(
                        radius_squared
                        - (circle_distance * circle_distance)
                    )

                    row_x0 = x + radius - corner_extent
                    row_x1 = (
                        x
                        + width
                        - radius
                        - 1
                        + corner_extent
                    )
                else:
                    row_x0 = x
                    row_x1 = x + width - 1

                row_x0 = max(row_x0, clipped_x0)
                row_x1 = min(row_x1, clipped_x1)

                if row_x0 > row_x1:
                    continue

                position = local_y

                red = start_red + (
                    (end_red - start_red) * position
                ) // denominator
                green = start_green + (
                    (end_green - start_green) * position
                ) // denominator
                blue = start_blue + (
                    (end_blue - start_blue) * position
                ) // denominator

                colour = self._components_to_rgb565(
                    red,
                    green,
                    blue
                )

                self.hline(
                    row_x0,
                    screen_y,
                    row_x1 - row_x0 + 1,
                    colour
                )

        else:
            denominator = max(1, width - 1)

            for screen_x in range(clipped_x0, clipped_x1 + 1):
                local_x = screen_x - x
                edge_distance = min(
                    local_x,
                    width - 1 - local_x
                )

                if edge_distance < radius:
                    circle_distance = radius - edge_distance
                    corner_extent = self._integer_sqrt(
                        radius_squared
                        - (circle_distance * circle_distance)
                    )

                    column_y0 = y + radius - corner_extent
                    column_y1 = (
                        y
                        + height
                        - radius
                        - 1
                        + corner_extent
                    )
                else:
                    column_y0 = y
                    column_y1 = y + height - 1

                column_y0 = max(column_y0, clipped_y0)
                column_y1 = min(column_y1, clipped_y1)

                if column_y0 > column_y1:
                    continue

                position = local_x

                red = start_red + (
                    (end_red - start_red) * position
                ) // denominator
                green = start_green + (
                    (end_green - start_green) * position
                ) // denominator
                blue = start_blue + (
                    (end_blue - start_blue) * position
                ) // denominator

                colour = self._components_to_rgb565(
                    red,
                    green,
                    blue
                )

                self.vline(
                    screen_x,
                    column_y0,
                    column_y1 - column_y0 + 1,
                    colour
                )

    @staticmethod
    def _scale_value(scale):
        """
        Validate and return an integer text scale of at least one.
        """
        scale = int(scale)

        if scale < 1:
            return 1

        return scale

    @staticmethod
    def _character_code(character):
        """
        Return a printable-ASCII code, replacing unsupported glyphs.
        """
        if isinstance(character, int):
            code = character
        else:
            character = str(character)

            if not character:
                code = REPLACEMENT_CHARACTER
            else:
                code = ord(character[0])

        if code < FIRST_CHARACTER or code > LAST_CHARACTER:
            return REPLACEMENT_CHARACTER

        return code

    def character(
        self,
        x,
        y,
        character,
        colour,
        background=None,
        scale=1
    ):
        """
        Draw one 8 x 8 bitmap character.

        Parameters
        ----------
        x, y : int
            Top-left coordinate.
        character
            Character string or integer character code.
        colour : int
            Foreground RGB565 colour.
        background : int or None
            RGB565 background colour. None leaves background pixels
            unchanged.
        scale : int
            Integer enlargement factor. Values below one become one.

        Returns
        -------
        int
            Rendered character width in pixels.
        """
        x = int(x)
        y = int(y)
        scale = self._scale_value(scale)

        glyph_width = FONT_WIDTH * scale
        glyph_height = FONT_HEIGHT * scale

        if background is not None:
            self.fill_rect(
                x,
                y,
                glyph_width,
                glyph_height,
                background
            )

        code = self._character_code(character)
        glyph_start = (
            code - FIRST_CHARACTER
        ) * FONT_HEIGHT

        for row in range(FONT_HEIGHT):
            row_bits = FONT_DATA[glyph_start + row]
            column = 0

            while column < FONT_WIDTH:
                bit_mask = 1 << (7 - column)

                if not (row_bits & bit_mask):
                    column += 1
                    continue

                run_start = column
                column += 1

                while column < FONT_WIDTH:
                    bit_mask = 1 << (7 - column)

                    if not (row_bits & bit_mask):
                        break

                    column += 1

                run_width = column - run_start

                if scale == 1:
                    self.hline(
                        x + run_start,
                        y + row,
                        run_width,
                        colour
                    )
                else:
                    self.fill_rect(
                        x + (run_start * scale),
                        y + (row * scale),
                        run_width * scale,
                        scale,
                        colour
                    )

        return glyph_width

    def text(
        self,
        text,
        x,
        y,
        colour,
        background=None,
        scale=1,
        spacing=1,
        line_spacing=1,
        wrap=False,
        tab_size=4
    ):
        """
        Draw a string and return the final cursor position.

        Parameters
        ----------
        text
            Object converted to a string.
        x, y : int
            Top-left starting coordinate.
        colour : int
            Foreground RGB565 colour.
        background : int or None
            Solid character-cell background, or None for transparency.
        scale : int
            Integer character scale.
        spacing : int
            Unscaled horizontal pixels between characters.
        line_spacing : int
            Unscaled vertical pixels between lines.
        wrap : bool
            Automatically begin a new line before a character that
            would extend beyond the right edge.
        tab_size : int
            Number of character advances per tab stop.

        Control characters
        ------------------
        \n  new line
        \r  return to the original x coordinate
        \t  advance to the next tab stop

        Returns
        -------
        tuple
            Final (x, y) cursor coordinate.
        """
        text = str(text)

        origin_x = int(x)
        cursor_x = origin_x
        cursor_y = int(y)

        scale = self._scale_value(scale)
        spacing = max(0, int(spacing))
        line_spacing = max(0, int(line_spacing))
        tab_size = max(1, int(tab_size))

        glyph_width = FONT_WIDTH * scale
        glyph_height = FONT_HEIGHT * scale
        character_advance = (
            FONT_WIDTH + spacing
        ) * scale
        line_advance = (
            FONT_HEIGHT + line_spacing
        ) * scale
        tab_advance = character_advance * tab_size

        for character in text:
            if character == "\n":
                cursor_x = origin_x
                cursor_y += line_advance
                continue

            if character == "\r":
                cursor_x = origin_x
                continue

            if character == "\t":
                relative_x = cursor_x - origin_x
                next_tab_x = origin_x + (
                    ((relative_x // tab_advance) + 1)
                    * tab_advance
                )

                if background is not None:
                    self.fill_rect(
                        cursor_x,
                        cursor_y,
                        next_tab_x - cursor_x,
                        glyph_height,
                        background
                    )

                cursor_x = next_tab_x
                continue

            if (
                wrap
                and cursor_x != origin_x
                and cursor_x + glyph_width > self.width
            ):
                cursor_x = origin_x
                cursor_y += line_advance

            # Once the cursor is wholly below the screen, later lines
            # cannot become visible.
            if cursor_y >= self.height:
                break

            self.character(
                cursor_x,
                cursor_y,
                character,
                colour,
                background=background,
                scale=scale
            )

            if background is not None and spacing > 0:
                self.fill_rect(
                    cursor_x + glyph_width,
                    cursor_y,
                    spacing * scale,
                    glyph_height,
                    background
                )

            cursor_x += character_advance

        return cursor_x, cursor_y

    def text_size(
        self,
        text,
        scale=1,
        spacing=1,
        line_spacing=1,
        tab_size=4
    ):
        """
        Measure text without drawing it.

        Returns the width and height of the smallest rectangular area
        containing all character cells.
        """
        text = str(text)

        if not text:
            return 0, 0

        scale = self._scale_value(scale)
        spacing = max(0, int(spacing))
        line_spacing = max(0, int(line_spacing))
        tab_size = max(1, int(tab_size))

        glyph_width = FONT_WIDTH * scale
        glyph_height = FONT_HEIGHT * scale
        spacing_width = spacing * scale
        character_advance = glyph_width + spacing_width
        line_advance = (
            FONT_HEIGHT + line_spacing
        ) * scale
        tab_advance = character_advance * tab_size

        cursor_x = 0
        maximum_width = 0
        line_has_character = False
        line_count = 1

        for character in text:
            if character == "\n":
                if line_has_character:
                    line_width = cursor_x - spacing_width
                else:
                    line_width = cursor_x

                if line_width > maximum_width:
                    maximum_width = line_width

                cursor_x = 0
                line_has_character = False
                line_count += 1
                continue

            if character == "\r":
                cursor_x = 0
                line_has_character = False
                continue

            if character == "\t":
                cursor_x = (
                    (cursor_x // tab_advance) + 1
                ) * tab_advance
                continue

            cursor_x += character_advance
            line_has_character = True

        if line_has_character:
            line_width = cursor_x - spacing_width
        else:
            line_width = cursor_x

        if line_width > maximum_width:
            maximum_width = line_width

        total_height = (
            glyph_height
            + ((line_count - 1) * line_advance)
        )

        return maximum_width, total_height

    def text_width(
        self,
        text,
        scale=1,
        spacing=1,
        tab_size=4
    ):
        """
        Return the maximum line width of a string.
        """
        width, _ = self.text_size(
            text,
            scale=scale,
            spacing=spacing,
            line_spacing=0,
            tab_size=tab_size
        )

        return width
