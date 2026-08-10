"""
touch.py
========

XPT2046-compatible resistive touchscreen driver for the MicroPython
Pyboard v1.1.

Version: 0.7.1

Designed for the common TFT breakout pins:

    T_CLK
    T_CS
    T_DIN
    T_DO
    T_IRQ

The touch controller shares SPI1 with the ILI9488 display:

    T_CLK -> SPI1 SCK  / X6
    T_DIN -> SPI1 MOSI / X8
    T_DO  -> SPI1 MISO / X7

Only chip select is unique:

    LCD CS   -> X5
    TOUCH CS -> X2

The optional interrupt pin is connected separately:

    T_IRQ -> X1

Shared-bus operation
--------------------
The ILI9488 can run at a substantially higher SPI clock than the
XPT2046. This driver temporarily changes the shared SPI bus to the touch
clock, performs a reading, then restores the display clock before
returning.

The LCD and touchscreen chip-select pins are never asserted together.

Calibration
-----------
A general three-point affine transform is used:

    screen_x = (a*raw_x + b*raw_y + c) / divisor
    screen_y = (d*raw_x + e*raw_y + f) / divisor

This automatically handles:

- exchanged X and Y axes
- reversed axes
- display rotation
- different raw minimum and maximum values
- moderate skew between the touch panel and LCD

Calibration remains specific to the display rotation used when the
three points were collected.
"""

try:
    from time import (
        sleep_ms,
        ticks_ms,
        ticks_diff
    )
except ImportError:
    from time import sleep, monotonic

    def sleep_ms(milliseconds):
        sleep(milliseconds / 1000.0)

    def ticks_ms():
        return int(monotonic() * 1000)

    def ticks_diff(new_value, old_value):
        return new_value - old_value


try:
    from micropython import const
except ImportError:
    def const(value):
        return value


# XPT2046 channel commands, 12-bit differential conversion,
# power-down between conversions so T_IRQ remains functional.
_CMD_Y = const(0x90)
_CMD_X = const(0xD0)
_CMD_Z1 = const(0xB0)
_CMD_Z2 = const(0xC0)


class Touch:
    """
    XPT2046-compatible resistive touchscreen.

    Parameters
    ----------
    spi
        Shared initialized SPI object.
    cs
        Touch-controller chip-select Pin.
    irq
        Optional active-low T_IRQ Pin.
    display_cs
        LCD chip-select Pin. It is forced inactive during touch reads.
    display_baudrate : int
        SPI clock restored after every touch transaction.
    touch_baudrate : int
        SPI clock used for XPT2046 transactions.
    pressure_threshold : int
        Minimum Z1 reading used only when no IRQ pin is supplied.
    calibration
        Optional seven-integer affine calibration tuple.
    width, height : int or None
        Screen dimensions used for clipping calibrated coordinates.
    debug : bool
        Print bus and calibration diagnostics when True.
    """

    __slots__ = (
        "spi",
        "cs",
        "irq",
        "display_cs",
        "display_baudrate",
        "touch_baudrate",
        "pressure_threshold",
        "width",
        "height",
        "debug",
        "_calibration",
        "_tx",
        "_rx"
    )

    def __init__(
        self,
        spi,
        cs,
        irq=None,
        display_cs=None,
        display_baudrate=10_000_000,
        touch_baudrate=1_000_000,
        pressure_threshold=80,
        calibration=None,
        width=None,
        height=None,
        debug=False
    ):
        self.spi = spi
        self.cs = cs
        self.irq = irq
        self.display_cs = display_cs

        self.display_baudrate = int(display_baudrate)
        self.touch_baudrate = int(touch_baudrate)
        self.pressure_threshold = int(pressure_threshold)

        self.width = (
            None
            if width is None
            else int(width)
        )

        self.height = (
            None
            if height is None
            else int(height)
        )

        self.debug = bool(debug)
        self._calibration = None

        self._tx = bytearray(3)
        self._rx = bytearray(3)

        self.cs.value(1)

        if self.display_cs is not None:
            self.display_cs.value(1)

        if calibration is not None:
            self.set_calibration(
                calibration,
                width=self.width,
                height=self.height
            )

    def _debug_print(self, message):
        if self.debug:
            print("[Touch]", message)

    def _configure_spi(self, baudrate):
        """
        Configure pyb.SPI or a compatible machine.SPI object.
        """
        initializer = getattr(self.spi, "init", None)

        if initializer is None:
            return

        spi_type = type(self.spi)
        master = getattr(spi_type, "MASTER", None)
        msb = getattr(spi_type, "MSB", None)

        if master is not None:
            arguments = {
                "baudrate": int(baudrate),
                "polarity": 0,
                "phase": 0
            }

            if msb is not None:
                arguments["firstbit"] = msb

            initializer(master, **arguments)
            return

        # machine.SPI style fallback.
        arguments = {
            "baudrate": int(baudrate),
            "polarity": 0,
            "phase": 0
        }

        if msb is not None:
            arguments["firstbit"] = msb

        initializer(**arguments)

    def _transfer(self):
        """
        Exchange the three-byte command transaction.
        """
        send_receive = getattr(
            self.spi,
            "send_recv",
            None
        )

        if send_receive is not None:
            send_receive(self._tx, self._rx)
            return

        write_readinto = getattr(
            self.spi,
            "write_readinto",
            None
        )

        if write_readinto is not None:
            write_readinto(self._tx, self._rx)
            return

        send = getattr(self.spi, "send", None)
        receive = getattr(self.spi, "recv", None)

        if send is not None and receive is not None:
            send(self._tx[0:1])
            received = receive(2)

            self._rx[0] = 0
            self._rx[1] = received[0]
            self._rx[2] = received[1]
            return

        raise RuntimeError(
            "SPI object does not provide a supported transfer method"
        )

    def _read_channel_unlocked(self, command):
        """
        Read one 12-bit channel while touch SPI mode is active.
        """
        self._tx[0] = command
        self._tx[1] = 0
        self._tx[2] = 0

        self.cs.value(0)

        try:
            self._transfer()
        finally:
            self.cs.value(1)

        return (
            ((self._rx[1] << 8) | self._rx[2])
            >> 3
        ) & 0x0FFF

    def _begin_touch_transaction(self):
        if self.display_cs is not None:
            self.display_cs.value(1)

        self.cs.value(1)
        self._configure_spi(self.touch_baudrate)

    def _end_touch_transaction(self):
        self.cs.value(1)

        if self.display_cs is not None:
            self.display_cs.value(1)

        self._configure_spi(self.display_baudrate)

    @staticmethod
    def _filtered_average(values):
        """
        Return a trimmed integer average of a small sample list.
        """
        count = len(values)

        if count == 0:
            return None

        values.sort()

        if count >= 5:
            start = 1
            end = count - 1
        else:
            start = 0
            end = count

        total = 0

        for index in range(start, end):
            total += values[index]

        return total // (end - start)

    def is_touched(self):
        """
        Return True while the panel is being pressed.

        T_IRQ is active low. When no IRQ pin is supplied, a single Z1
        conversion is used instead.
        """
        if self.irq is not None:
            return self.irq.value() == 0

        self._begin_touch_transaction()

        try:
            pressure = self._read_channel_unlocked(_CMD_Z1)
        finally:
            self._end_touch_transaction()

        return pressure >= self.pressure_threshold

    def read_raw(self, samples=7, require_touch=True):
        """
        Return filtered raw coordinates as (raw_x, raw_y, z1).

        Returns None when require_touch is True and no valid contact is
        detected.

        Parameters
        ----------
        samples : int
            Number of coordinate pairs. Values from 5 to 15 are useful.
        require_touch : bool
            Check T_IRQ or Z1 before accepting a reading.
        """
        samples = max(1, int(samples))

        if require_touch and not self.is_touched():
            return None

        x_values = []
        y_values = []
        z1_values = []

        self._begin_touch_transaction()

        try:
            # The first conversion after a long idle period can be less
            # stable. Discard one X and Y conversion.
            self._read_channel_unlocked(_CMD_X)
            self._read_channel_unlocked(_CMD_Y)

            for _ in range(samples):
                if (
                    require_touch
                    and self.irq is not None
                    and self.irq.value() != 0
                ):
                    break

                raw_x = self._read_channel_unlocked(_CMD_X)
                raw_y = self._read_channel_unlocked(_CMD_Y)
                z1 = self._read_channel_unlocked(_CMD_Z1)

                if (
                    self.irq is None
                    and z1 < self.pressure_threshold
                ):
                    continue

                x_values.append(raw_x)
                y_values.append(raw_y)
                z1_values.append(z1)

        finally:
            self._end_touch_transaction()

        if not x_values:
            return None

        raw_x = self._filtered_average(x_values)
        raw_y = self._filtered_average(y_values)
        z1 = self._filtered_average(z1_values)

        return raw_x, raw_y, z1

    @staticmethod
    def _rounded_divide(numerator, denominator):
        """
        Divide integers with symmetric rounding and no floating point.
        """
        if denominator == 0:
            raise ZeroDivisionError(
                "touch calibration divisor is zero"
            )

        negative = (
            (numerator < 0)
            != (denominator < 0)
        )

        numerator = abs(numerator)
        denominator = abs(denominator)

        result = (
            numerator + (denominator // 2)
        ) // denominator

        return -result if negative else result

    @staticmethod
    def calculate_calibration(
        raw_points,
        screen_points
    ):
        """
        Calculate a seven-integer affine calibration tuple.

        raw_points and screen_points must each contain exactly three
        non-collinear (x, y) coordinate pairs.
        """
        if (
            len(raw_points) != 3
            or len(screen_points) != 3
        ):
            raise ValueError(
                "calibration requires exactly three point pairs"
            )

        raw_x0, raw_y0 = raw_points[0]
        raw_x1, raw_y1 = raw_points[1]
        raw_x2, raw_y2 = raw_points[2]

        screen_x0, screen_y0 = screen_points[0]
        screen_x1, screen_y1 = screen_points[1]
        screen_x2, screen_y2 = screen_points[2]

        divisor = (
            raw_x0 * (raw_y1 - raw_y2)
            + raw_x1 * (raw_y2 - raw_y0)
            + raw_x2 * (raw_y0 - raw_y1)
        )

        if divisor == 0:
            raise ValueError(
                "raw calibration points are collinear"
            )

        coefficient_a = (
            screen_x0 * (raw_y1 - raw_y2)
            + screen_x1 * (raw_y2 - raw_y0)
            + screen_x2 * (raw_y0 - raw_y1)
        )

        coefficient_b = (
            screen_x0 * (raw_x2 - raw_x1)
            + screen_x1 * (raw_x0 - raw_x2)
            + screen_x2 * (raw_x1 - raw_x0)
        )

        coefficient_c = (
            screen_x0
            * (
                raw_x1 * raw_y2
                - raw_x2 * raw_y1
            )
            + screen_x1
            * (
                raw_x2 * raw_y0
                - raw_x0 * raw_y2
            )
            + screen_x2
            * (
                raw_x0 * raw_y1
                - raw_x1 * raw_y0
            )
        )

        coefficient_d = (
            screen_y0 * (raw_y1 - raw_y2)
            + screen_y1 * (raw_y2 - raw_y0)
            + screen_y2 * (raw_y0 - raw_y1)
        )

        coefficient_e = (
            screen_y0 * (raw_x2 - raw_x1)
            + screen_y1 * (raw_x0 - raw_x2)
            + screen_y2 * (raw_x1 - raw_x0)
        )

        coefficient_f = (
            screen_y0
            * (
                raw_x1 * raw_y2
                - raw_x2 * raw_y1
            )
            + screen_y1
            * (
                raw_x2 * raw_y0
                - raw_x0 * raw_y2
            )
            + screen_y2
            * (
                raw_x0 * raw_y1
                - raw_x1 * raw_y0
            )
        )

        return (
            coefficient_a,
            coefficient_b,
            coefficient_c,
            coefficient_d,
            coefficient_e,
            coefficient_f,
            divisor
        )

    def set_calibration(
        self,
        calibration,
        width=None,
        height=None
    ):
        """
        Install an affine calibration tuple.
        """
        if calibration is None:
            self._calibration = None
            return

        if len(calibration) != 7:
            raise ValueError(
                "calibration must contain seven integers"
            )

        calibration = tuple(
            int(value)
            for value in calibration
        )

        if calibration[6] == 0:
            raise ValueError(
                "calibration divisor cannot be zero"
            )

        self._calibration = calibration

        if width is not None:
            self.width = int(width)

        if height is not None:
            self.height = int(height)

        self._debug_print(
            "Calibration installed: {}".format(
                calibration
            )
        )

    def clear_calibration(self):
        """Remove the current calibration."""
        self._calibration = None

    @property
    def calibrated(self):
        """Return True when a calibration transform is installed."""
        return self._calibration is not None

    @property
    def calibration(self):
        """Return the current immutable calibration tuple."""
        return self._calibration

    def map_raw(self, raw_x, raw_y):
        """
        Convert raw controller coordinates into screen coordinates.
        """
        if self._calibration is None:
            raise RuntimeError(
                "touchscreen has not been calibrated"
            )

        (
            coefficient_a,
            coefficient_b,
            coefficient_c,
            coefficient_d,
            coefficient_e,
            coefficient_f,
            divisor
        ) = self._calibration

        screen_x = self._rounded_divide(
            coefficient_a * int(raw_x)
            + coefficient_b * int(raw_y)
            + coefficient_c,
            divisor
        )

        screen_y = self._rounded_divide(
            coefficient_d * int(raw_x)
            + coefficient_e * int(raw_y)
            + coefficient_f,
            divisor
        )

        if self.width is not None:
            screen_x = max(
                0,
                min(self.width - 1, screen_x)
            )

        if self.height is not None:
            screen_y = max(
                0,
                min(self.height - 1, screen_y)
            )

        return screen_x, screen_y

    def read(self, samples=7):
        """
        Return calibrated (x, y, z1), or None when not touched.
        """
        raw = self.read_raw(
            samples=samples,
            require_touch=True
        )

        if raw is None:
            return None

        if self._calibration is None:
            raise RuntimeError(
                "touchscreen has not been calibrated"
            )

        raw_x, raw_y, z1 = raw
        screen_x, screen_y = self.map_raw(
            raw_x,
            raw_y
        )

        return screen_x, screen_y, z1

    def wait_for_touch(
        self,
        timeout_ms=None,
        poll_ms=10
    ):
        """
        Wait for a press and return True, or False on timeout.
        """
        start = ticks_ms()

        while not self.is_touched():
            if (
                timeout_ms is not None
                and ticks_diff(ticks_ms(), start)
                >= int(timeout_ms)
            ):
                return False

            sleep_ms(poll_ms)

        return True

    def wait_for_release(
        self,
        timeout_ms=None,
        poll_ms=10
    ):
        """
        Wait for release and return True, or False on timeout.
        """
        start = ticks_ms()

        while self.is_touched():
            if (
                timeout_ms is not None
                and ticks_diff(ticks_ms(), start)
                >= int(timeout_ms)
            ):
                return False

            sleep_ms(poll_ms)

        return True

    def save_calibration(
        self,
        path,
        rotation=0
    ):
        """
        Save the current calibration as an importable Python module.
        """
        if self._calibration is None:
            raise RuntimeError(
                "cannot save an empty calibration"
            )

        with open(path, "w") as file:
            file.write(
                '"""Auto-generated touchscreen calibration."""\n\n'
            )

            file.write(
                "CALIBRATION = {}\n".format(
                    repr(self._calibration)
                )
            )

            file.write(
                "WIDTH = {}\n".format(
                    repr(self.width)
                )
            )

            file.write(
                "HEIGHT = {}\n".format(
                    repr(self.height)
                )
            )

            file.write(
                "ROTATION = {}\n".format(
                    int(rotation) & 0x03
                )
            )
