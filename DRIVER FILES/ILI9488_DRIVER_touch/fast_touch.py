"""
fast_touch.py
=============

Low-overhead calibrated touch polling for interactive drawing.

Version: 0.7.1

The normal Touch.read(samples=5) path performs X, Y and Z1 conversions
for every sample. That is desirable for robust general-purpose input,
but the paint program already has an active-low T_IRQ signal and does
not need a pressure reading.

FastTouchReader therefore:

- uses T_IRQ for contact detection
- reads only X and Y
- uses a three-sample median
- discards a warm-up pair only at the start of each new press
- restores the LCD SPI speed before returning

MicroPython const note
----------------------
The XPT2046 command bytes are deliberately defined locally.

MicroPython can remove module-level const() names beginning with an
underscore from the module's runtime globals. Consequently, importing
touch.py's private _CMD_X and _CMD_Y names can fail even though touch.py
uses those constants internally without a problem.

Keeping the two command bytes local avoids that implementation-specific
import failure.
"""

# XPT2046 channel commands:
#
# 0xD0 = X-position conversion
# 0x90 = Y-position conversion
#
# Plain integer constants are intentional. They are tiny and avoid
# depending on private names from touch.py.
_CMD_X = 0xD0
_CMD_Y = 0x90


class FastTouchReader:
    """Stateful low-overhead reader for a calibrated Touch object."""

    __slots__ = (
        "touch",
        "active",
    )

    def __init__(self, touch):
        if touch.irq is None:
            raise ValueError(
                "FastTouchReader requires the T_IRQ connection"
            )

        self.touch = touch
        self.active = False

    @staticmethod
    def _median3(value0, value1, value2):
        """Return the median of three integers without allocating."""
        if value0 > value1:
            value0, value1 = value1, value0

        if value1 > value2:
            value1, value2 = value2, value1

        if value0 > value1:
            value0, value1 = value1, value0

        return value1

    def read(self):
        """
        Return calibrated (x, y), or None when the panel is released.
        """
        touch = self.touch

        if touch.irq.value() != 0:
            self.active = False
            return None

        touch._begin_touch_transaction()

        try:
            if not self.active:
                # Discard the first pair after a new press.
                touch._read_channel_unlocked(_CMD_X)
                touch._read_channel_unlocked(_CMD_Y)

            x0 = touch._read_channel_unlocked(_CMD_X)
            y0 = touch._read_channel_unlocked(_CMD_Y)

            x1 = touch._read_channel_unlocked(_CMD_X)
            y1 = touch._read_channel_unlocked(_CMD_Y)

            x2 = touch._read_channel_unlocked(_CMD_X)
            y2 = touch._read_channel_unlocked(_CMD_Y)

        finally:
            touch._end_touch_transaction()

        self.active = True

        raw_x = self._median3(
            x0,
            x1,
            x2,
        )

        raw_y = self._median3(
            y0,
            y1,
            y2,
        )

        return touch.map_raw(
            raw_x,
            raw_y,
        )
