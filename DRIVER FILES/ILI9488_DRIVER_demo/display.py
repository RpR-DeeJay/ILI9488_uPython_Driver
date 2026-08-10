"""
display.py
==========

Low-level MicroPython driver for a 320 x 480 SPI TFT using an ILI9488
display controller.

Version: 0.7.0
Target:  MicroPython Pyboard v1.1
Bus:     SPI1

Implemented features
--------------------
- Hardware reset and ILI9488 initialization
- Four display rotations
- RGB565 public colour interface
- RGB666 SPI transmission required by the ILI9488
- Pixels, fills, horizontal lines and vertical lines
- Fast opaque RGB565 image-buffer transfers
- Destination clipping
- Source stride and source-offset support
- Optional RGB565 colour-key transparency
- Big-endian and little-endian RGB565 source data

The display controller expects three transmitted bytes per pixel in its
SPI RGB666 mode. Image and sprite data remain compact RGB565 in memory;
the driver converts them into RGB666 in reusable chunks while sending.
"""

try:
    from time import sleep_ms
except ImportError:
    from time import sleep

    def sleep_ms(milliseconds):
        sleep(milliseconds / 1000.0)

try:
    from micropython import const
except ImportError:
    def const(value):
        return value


_SOFTWARE_RESET = const(0x01)
_SLEEP_OUT = const(0x11)
_DISPLAY_ON = const(0x29)
_COLUMN_ADDRESS_SET = const(0x2A)
_PAGE_ADDRESS_SET = const(0x2B)
_MEMORY_WRITE = const(0x2C)
_MEMORY_ACCESS_CONTROL = const(0x36)
_PIXEL_FORMAT_SET = const(0x3A)
_INTERFACE_MODE_CONTROL = const(0xB0)
_FRAME_RATE_CONTROL_NORMAL = const(0xB1)
_DISPLAY_INVERSION_CONTROL = const(0xB4)
_DISPLAY_FUNCTION_CONTROL = const(0xB6)
_POWER_CONTROL_1 = const(0xC0)
_POWER_CONTROL_2 = const(0xC1)
_VCOM_CONTROL_1 = const(0xC5)
_POSITIVE_GAMMA_CONTROL = const(0xE0)
_NEGATIVE_GAMMA_CONTROL = const(0xE1)
_ADJUST_CONTROL_3 = const(0xF7)
_SET_IMAGE_FUNCTION = const(0xE9)

_MADCTL_MY = const(0x80)
_MADCTL_MX = const(0x40)
_MADCTL_MV = const(0x20)
_MADCTL_BGR = const(0x08)


class Display:
    """
    Low-level SPI display driver.

    Parameters
    ----------
    spi
        Initialized MicroPython SPI object.
    cs, dc, rst
        Initialized output Pin objects.
    width, height : int
        Native display dimensions.
    rotation : int
        Initial rotation from 0 through 3.
    debug : bool
        Print initialization information when True.
    buffer_pixels : int
        Number of pixels converted in each reusable transfer chunk.
    """

    def __init__(
        self,
        spi,
        cs,
        dc,
        rst,
        width=320,
        height=480,
        rotation=0,
        debug=False,
        buffer_pixels=256
    ):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst

        self.native_width = int(width)
        self.native_height = int(height)

        self.width = self.native_width
        self.height = self.native_height
        self.rotation = 0

        self.debug = bool(debug)

        buffer_pixels = max(1, int(buffer_pixels))

        # Reused both for same-colour fills and RGB565-to-RGB666 image
        # conversion. Three bytes are transmitted for every pixel.
        self._transfer_buffer = bytearray(buffer_pixels * 3)
        self._transfer_view = memoryview(self._transfer_buffer)

        self._single_byte = bytearray(1)
        self._window_buffer = bytearray(4)

        self.cs.value(1)
        self.dc.value(1)
        self.rst.value(1)

        self._requested_rotation = int(rotation) & 0x03

    def _debug_print(self, message):
        if self.debug:
            print("[Display]", message)

    def _spi_write(self, data):
        try:
            self.spi.write(data)
        except AttributeError:
            self.spi.send(data)

    def _write_command(self, command, data=None):
        self.cs.value(0)

        self.dc.value(0)
        self._single_byte[0] = command & 0xFF
        self._spi_write(self._single_byte)

        if data is not None and len(data):
            self.dc.value(1)
            self._spi_write(data)

        self.cs.value(1)

    def _hardware_reset(self):
        self.cs.value(1)
        self.dc.value(1)

        self.rst.value(1)
        sleep_ms(10)

        self.rst.value(0)
        sleep_ms(20)

        self.rst.value(1)
        sleep_ms(150)

    def begin(self):
        """Reset and initialize the ILI9488 controller."""
        self._debug_print("Beginning display initialization")
        self._hardware_reset()

        self._write_command(_SOFTWARE_RESET)
        sleep_ms(150)

        self._write_command(
            _POSITIVE_GAMMA_CONTROL,
            bytes((
                0x00, 0x03, 0x09, 0x08,
                0x16, 0x0A, 0x3F, 0x78,
                0x4C, 0x09, 0x0A, 0x08,
                0x16, 0x1A, 0x0F
            ))
        )

        self._write_command(
            _NEGATIVE_GAMMA_CONTROL,
            bytes((
                0x00, 0x16, 0x19, 0x03,
                0x0F, 0x05, 0x32, 0x45,
                0x46, 0x04, 0x0E, 0x0D,
                0x35, 0x37, 0x0F
            ))
        )

        self._write_command(_POWER_CONTROL_1, bytes((0x17, 0x15)))
        self._write_command(_POWER_CONTROL_2, bytes((0x41,)))
        self._write_command(_VCOM_CONTROL_1, bytes((0x00, 0x12, 0x80)))
        self._write_command(_INTERFACE_MODE_CONTROL, bytes((0x00,)))

        # ILI9488 SPI pixel data uses three-byte RGB666 transfers.
        self._write_command(_PIXEL_FORMAT_SET, bytes((0x66,)))

        self._write_command(_FRAME_RATE_CONTROL_NORMAL, bytes((0xA0,)))
        self._write_command(_DISPLAY_INVERSION_CONTROL, bytes((0x02,)))
        self._write_command(_DISPLAY_FUNCTION_CONTROL, bytes((0x02, 0x02)))
        self._write_command(_SET_IMAGE_FUNCTION, bytes((0x00,)))
        self._write_command(
            _ADJUST_CONTROL_3,
            bytes((0xA9, 0x51, 0x2C, 0x82))
        )

        self.set_rotation(self._requested_rotation)

        self._write_command(_SLEEP_OUT)
        sleep_ms(150)

        self._write_command(_DISPLAY_ON)
        sleep_ms(50)

        self._debug_print(
            "Initialization complete: {} x {}".format(
                self.width,
                self.height
            )
        )

    def set_rotation(self, rotation):
        """
        Set the display orientation.

        0 = 320 x 480 portrait
        1 = 480 x 320 landscape
        2 = reversed portrait
        3 = reversed landscape
        """
        rotation = int(rotation) & 0x03
        self.rotation = rotation

        if rotation == 0:
            madctl = _MADCTL_MX | _MADCTL_BGR
            self.width = self.native_width
            self.height = self.native_height

        elif rotation == 1:
            madctl = _MADCTL_MV | _MADCTL_BGR
            self.width = self.native_height
            self.height = self.native_width

        elif rotation == 2:
            madctl = _MADCTL_MY | _MADCTL_BGR
            self.width = self.native_width
            self.height = self.native_height

        else:
            madctl = (
                _MADCTL_MX
                | _MADCTL_MY
                | _MADCTL_MV
                | _MADCTL_BGR
            )
            self.width = self.native_height
            self.height = self.native_width

        self._write_command(
            _MEMORY_ACCESS_CONTROL,
            bytes((madctl,))
        )

    def set_window(self, x0, y0, x1, y1):
        """Set the inclusive rectangular drawing window."""
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)

        buffer_data = self._window_buffer

        buffer_data[0] = (x0 >> 8) & 0xFF
        buffer_data[1] = x0 & 0xFF
        buffer_data[2] = (x1 >> 8) & 0xFF
        buffer_data[3] = x1 & 0xFF
        self._write_command(_COLUMN_ADDRESS_SET, buffer_data)

        buffer_data[0] = (y0 >> 8) & 0xFF
        buffer_data[1] = y0 & 0xFF
        buffer_data[2] = (y1 >> 8) & 0xFF
        buffer_data[3] = y1 & 0xFF
        self._write_command(_PAGE_ADDRESS_SET, buffer_data)

    @staticmethod
    def _normalise_byteorder(byteorder):
        if byteorder in ("big", "be", "BE", ">"):
            return True

        if byteorder in ("little", "le", "LE", "<"):
            return False

        raise ValueError("byteorder must be 'big' or 'little'")

    @staticmethod
    def _rgb565_to_rgb666(colour):
        colour &= 0xFFFF

        red_5 = (colour >> 11) & 0x1F
        green_6 = (colour >> 5) & 0x3F
        blue_5 = colour & 0x1F

        red_8 = (red_5 << 3) | (red_5 >> 2)
        green_8 = (green_6 << 2) | (green_6 >> 4)
        blue_8 = (blue_5 << 3) | (blue_5 >> 2)

        return (
            red_8 & 0xFC,
            green_8 & 0xFC,
            blue_8 & 0xFC
        )

    @staticmethod
    def _read_rgb565(data, byte_index, big_endian):
        if big_endian:
            return (
                (data[byte_index] << 8)
                | data[byte_index + 1]
            )

        return (
            data[byte_index]
            | (data[byte_index + 1] << 8)
        )

    def _begin_memory_write(self):
        self.cs.value(0)
        self.dc.value(0)

        self._single_byte[0] = _MEMORY_WRITE
        self._spi_write(self._single_byte)

        self.dc.value(1)

    def _end_memory_write(self):
        self.cs.value(1)

    def _prepare_colour_buffer(self, colour):
        red, green, blue = self._rgb565_to_rgb666(colour)
        transfer = self._transfer_buffer

        for index in range(0, len(transfer), 3):
            transfer[index] = red
            transfer[index + 1] = green
            transfer[index + 2] = blue

    def _write_repeated_colour(self, colour, pixel_count):
        pixel_count = int(pixel_count)

        if pixel_count <= 0:
            return

        self._prepare_colour_buffer(colour)

        pixels_per_buffer = len(self._transfer_buffer) // 3
        full_buffers = pixel_count // pixels_per_buffer
        remaining_pixels = pixel_count % pixels_per_buffer

        self._begin_memory_write()

        for _ in range(full_buffers):
            self._spi_write(self._transfer_buffer)

        if remaining_pixels:
            self._spi_write(
                self._transfer_view[:remaining_pixels * 3]
            )

        self._end_memory_write()

    def _write_rgb565_pixels(
        self,
        data,
        pixel_count=None,
        byteorder="big"
    ):
        """
        Convert and send a contiguous RGB565 pixel sequence.

        A drawing window must already have been selected.
        """
        source = memoryview(data)

        if pixel_count is None:
            pixel_count = len(source) // 2

        pixel_count = int(pixel_count)

        if pixel_count <= 0:
            return

        if len(source) < pixel_count * 2:
            raise ValueError("RGB565 buffer is smaller than pixel_count")

        big_endian = self._normalise_byteorder(byteorder)

        transfer = self._transfer_buffer
        transfer_view = self._transfer_view
        pixels_per_chunk = len(transfer) // 3

        source_pixel = 0
        remaining = pixel_count

        self._begin_memory_write()

        while remaining:
            chunk_pixels = min(remaining, pixels_per_chunk)

            for pixel_index in range(chunk_pixels):
                source_index = (source_pixel + pixel_index) * 2

                colour = self._read_rgb565(
                    source,
                    source_index,
                    big_endian
                )

                red_5 = (colour >> 11) & 0x1F
                green_6 = (colour >> 5) & 0x3F
                blue_5 = colour & 0x1F

                transfer_index = pixel_index * 3

                transfer[transfer_index] = (
                    ((red_5 << 3) | (red_5 >> 2))
                    & 0xFC
                )
                transfer[transfer_index + 1] = (
                    ((green_6 << 2) | (green_6 >> 4))
                    & 0xFC
                )
                transfer[transfer_index + 2] = (
                    ((blue_5 << 3) | (blue_5 >> 2))
                    & 0xFC
                )

            self._spi_write(
                transfer_view[:chunk_pixels * 3]
            )

            source_pixel += chunk_pixels
            remaining -= chunk_pixels

        self._end_memory_write()

    def fill(self, colour):
        """Fill the entire active display."""
        self.fill_rect(
            0,
            0,
            self.width,
            self.height,
            colour
        )

    def fill_rect(self, x, y, width, height, colour):
        """Draw a clipped filled rectangle."""
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            return

        x1 = x + width - 1
        y1 = y + height - 1

        if (
            x >= self.width
            or y >= self.height
            or x1 < 0
            or y1 < 0
        ):
            return

        if x < 0:
            x = 0

        if y < 0:
            y = 0

        if x1 >= self.width:
            x1 = self.width - 1

        if y1 >= self.height:
            y1 = self.height - 1

        self.set_window(x, y, x1, y1)

        self._write_repeated_colour(
            colour,
            (x1 - x + 1) * (y1 - y + 1)
        )

    def pixel(self, x, y, colour):
        """Draw one clipped pixel."""
        x = int(x)
        y = int(y)

        if 0 <= x < self.width and 0 <= y < self.height:
            self.set_window(x, y, x, y)
            self._write_repeated_colour(colour, 1)

    def hline(self, x, y, length, colour):
        """Draw a horizontal line."""
        self.fill_rect(x, y, length, 1, colour)

    def vline(self, x, y, length, colour):
        """Draw a vertical line."""
        self.fill_rect(x, y, 1, length, colour)

    def blit_rgb565(
        self,
        buffer,
        x,
        y,
        width,
        height,
        stride=None,
        offset=0,
        byteorder="big",
        transparent=None
    ):
        """
        Draw RGB565 image data from a bytes-like object.

        Parameters
        ----------
        buffer
            Source RGB565 bytes.
        x, y : int
            Destination top-left coordinate.
        width, height : int
            Source region dimensions.
        stride : int or None
            Complete source row width in pixels. Defaults to width.
        offset : int
            Source offset in pixels before the first requested pixel.
        byteorder : str
            'big' or 'little'.
        transparent : int or None
            RGB565 colour key. Matching pixels are not written.

        Returns
        -------
        tuple
            Actual visible width and height.
        """
        source = memoryview(buffer)

        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)
        offset = int(offset)

        if width <= 0 or height <= 0:
            return 0, 0

        if stride is None:
            stride = width

        stride = int(stride)

        if stride < width:
            raise ValueError("stride cannot be smaller than width")

        if offset < 0:
            raise ValueError("offset cannot be negative")

        required_pixels = (
            offset
            + ((height - 1) * stride)
            + width
        )

        if required_pixels * 2 > len(source):
            raise ValueError("RGB565 source region exceeds buffer")

        source_x = 0
        source_y = 0
        draw_width = width
        draw_height = height

        if x < 0:
            source_x = -x
            draw_width -= source_x
            x = 0

        if y < 0:
            source_y = -y
            draw_height -= source_y
            y = 0

        if x + draw_width > self.width:
            draw_width = self.width - x

        if y + draw_height > self.height:
            draw_height = self.height - y

        if draw_width <= 0 or draw_height <= 0:
            return 0, 0

        first_pixel = (
            offset
            + (source_y * stride)
            + source_x
        )

        if transparent is None:
            if stride == draw_width:
                start_byte = first_pixel * 2
                pixel_count = draw_width * draw_height

                self.set_window(
                    x,
                    y,
                    x + draw_width - 1,
                    y + draw_height - 1
                )

                self._write_rgb565_pixels(
                    source[
                        start_byte:
                        start_byte + (pixel_count * 2)
                    ],
                    pixel_count,
                    byteorder
                )

            else:
                for row in range(draw_height):
                    row_pixel = first_pixel + (row * stride)
                    row_byte = row_pixel * 2

                    self.set_window(
                        x,
                        y + row,
                        x + draw_width - 1,
                        y + row
                    )

                    self._write_rgb565_pixels(
                        source[
                            row_byte:
                            row_byte + (draw_width * 2)
                        ],
                        draw_width,
                        byteorder
                    )

            return draw_width, draw_height

        transparent &= 0xFFFF
        big_endian = self._normalise_byteorder(byteorder)

        for row in range(draw_height):
            row_pixel = first_pixel + (row * stride)
            column = 0

            while column < draw_width:
                source_byte = (row_pixel + column) * 2
                colour = self._read_rgb565(
                    source,
                    source_byte,
                    big_endian
                )

                if colour == transparent:
                    column += 1
                    continue

                run_start = column
                column += 1

                while column < draw_width:
                    source_byte = (row_pixel + column) * 2
                    colour = self._read_rgb565(
                        source,
                        source_byte,
                        big_endian
                    )

                    if colour == transparent:
                        break

                    column += 1

                run_length = column - run_start
                run_pixel = row_pixel + run_start
                run_byte = run_pixel * 2

                self.set_window(
                    x + run_start,
                    y + row,
                    x + run_start + run_length - 1,
                    y + row
                )

                self._write_rgb565_pixels(
                    source[
                        run_byte:
                        run_byte + (run_length * 2)
                    ],
                    run_length,
                    byteorder
                )

        return draw_width, draw_height
