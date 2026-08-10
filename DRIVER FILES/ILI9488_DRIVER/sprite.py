"""
sprite.py
=========

Memory-conscious RGB565 off-screen drawing buffers for the ILI9488
library.

Version: 0.7.0

A Sprite implements the same basic drawing-target interface used by
Graphics:

    pixel()
    fill()
    fill_rect()
    hline()
    vline()
    width
    height

The existing Graphics class can therefore draw all shapes and text into
a sprite before that sprite is transferred to the physical display.

Memory use
----------
Every sprite pixel occupies two bytes:

    memory = width * height * 2

Examples:

    32 x 32   = 2,048 bytes
    64 x 64   = 8,192 bytes
    120 x 80  = 19,200 bytes

Version 0.7.0 avoids creating a second full-size temporary object while
initializing or clearing a sprite. This is important on the Pyboard
v1.1, where a large temporary allocation can raise MemoryError even
when the final sprite buffer itself would fit.
"""


class Sprite:
    """
    Mutable big-endian RGB565 off-screen image.

    Parameters
    ----------
    width, height : int
        Sprite dimensions.
    background : int
        Initial RGB565 fill colour.
    transparent : int or None
        Default RGB565 colour key used when drawing the sprite.
    buffer
        Optional existing big-endian RGB565 bytes-like object.
    """

    __slots__ = (
        "width",
        "height",
        "buffer",
        "transparent"
    )

    @staticmethod
    def required_bytes(width, height):
        """
        Return the RGB565 buffer size required by given dimensions.
        """
        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            return 0

        return width * height * 2

    def __init__(
        self,
        width,
        height,
        background=0,
        transparent=None,
        buffer=None
    ):
        self.width = int(width)
        self.height = int(height)

        if self.width <= 0 or self.height <= 0:
            raise ValueError("sprite dimensions must be positive")

        required_bytes = self.required_bytes(self.width, self.height)

        if buffer is None:
            self.buffer = bytearray(required_bytes)
            self.fill(background)
        else:
            if len(buffer) != required_bytes:
                raise ValueError(
                    "buffer size must equal width * height * 2"
                )

            # Adopt an existing bytearray without duplicating it.
            # Immutable bytes and other objects are copied.
            if isinstance(buffer, bytearray):
                self.buffer = buffer
            else:
                self.buffer = bytearray(buffer)

        if transparent is None:
            self.transparent = None
        else:
            self.transparent = int(transparent) & 0xFFFF

    @property
    def memory_bytes(self):
        """Return the mutable pixel-buffer size in bytes."""
        return len(self.buffer)

    @staticmethod
    def _normalise_byteorder(byteorder):
        if byteorder in ("big", "be", "BE", ">"):
            return True

        if byteorder in ("little", "le", "LE", "<"):
            return False

        raise ValueError("byteorder must be 'big' or 'little'")

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

    @staticmethod
    def _write_colour(buffer, byte_index, colour):
        colour &= 0xFFFF
        buffer[byte_index] = (colour >> 8) & 0xFF
        buffer[byte_index + 1] = colour & 0xFF

    def pixel(self, x, y, colour):
        """Draw one clipped pixel into the sprite."""
        x = int(x)
        y = int(y)

        if 0 <= x < self.width and 0 <= y < self.height:
            byte_index = ((y * self.width) + x) * 2

            self._write_colour(
                self.buffer,
                byte_index,
                colour
            )

    def get_pixel(self, x, y):
        """Return one RGB565 pixel, or None outside the sprite."""
        x = int(x)
        y = int(y)

        if not (
            0 <= x < self.width
            and 0 <= y < self.height
        ):
            return None

        byte_index = ((y * self.width) + x) * 2

        return (
            (self.buffer[byte_index] << 8)
            | self.buffer[byte_index + 1]
        )

    def fill(self, colour):
        """
        Fill the complete sprite without a full-size temporary buffer.
        """
        colour = int(colour) & 0xFFFF

        high_byte = (colour >> 8) & 0xFF
        low_byte = colour & 0xFF

        buffer_data = self.buffer

        for byte_index in range(0, len(buffer_data), 2):
            buffer_data[byte_index] = high_byte
            buffer_data[byte_index + 1] = low_byte

    def clear(self, colour=0):
        """Alias for fill()."""
        self.fill(colour)

    def fill_rect(self, x, y, width, height, colour):
        """
        Draw a clipped filled rectangle without row-sized allocations.
        """
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            return

        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + width)
        y1 = min(self.height, y + height)

        if x0 >= x1 or y0 >= y1:
            return

        colour = int(colour) & 0xFFFF
        high_byte = (colour >> 8) & 0xFF
        low_byte = colour & 0xFF

        buffer_data = self.buffer
        sprite_width = self.width

        for screen_y in range(y0, y1):
            byte_index = (
                (screen_y * sprite_width) + x0
            ) * 2

            row_end = (
                (screen_y * sprite_width) + x1
            ) * 2

            while byte_index < row_end:
                buffer_data[byte_index] = high_byte
                buffer_data[byte_index + 1] = low_byte
                byte_index += 2

    def hline(self, x, y, length, colour):
        """
        Draw a clipped horizontal line without temporary allocations.
        """
        x = int(x)
        y = int(y)
        length = int(length)

        if (
            length <= 0
            or y < 0
            or y >= self.height
        ):
            return

        x0 = max(0, x)
        x1 = min(self.width, x + length)

        if x0 >= x1:
            return

        colour = int(colour) & 0xFFFF
        high_byte = (colour >> 8) & 0xFF
        low_byte = colour & 0xFF

        byte_index = (
            (y * self.width) + x0
        ) * 2

        byte_end = (
            (y * self.width) + x1
        ) * 2

        buffer_data = self.buffer

        while byte_index < byte_end:
            buffer_data[byte_index] = high_byte
            buffer_data[byte_index + 1] = low_byte
            byte_index += 2

    def vline(self, x, y, length, colour):
        """
        Draw a clipped vertical line without temporary allocations.
        """
        x = int(x)
        y = int(y)
        length = int(length)

        if (
            length <= 0
            or x < 0
            or x >= self.width
        ):
            return

        y0 = max(0, y)
        y1 = min(self.height, y + length)

        if y0 >= y1:
            return

        colour = int(colour) & 0xFFFF
        high_byte = (colour >> 8) & 0xFF
        low_byte = colour & 0xFF

        buffer_data = self.buffer
        row_step = self.width * 2

        byte_index = (
            (y0 * self.width) + x
        ) * 2

        for _ in range(y0, y1):
            buffer_data[byte_index] = high_byte
            buffer_data[byte_index + 1] = low_byte
            byte_index += row_step

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
        Copy RGB565 data into the sprite.

        The signature matches Display.blit_rgb565(), allowing image
        loaders to target either a physical display or a sprite.
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

        big_endian = self._normalise_byteorder(byteorder)

        for row in range(draw_height):
            source_pixel = first_pixel + (row * stride)
            destination_pixel = (
                ((y + row) * self.width) + x
            )

            if big_endian and transparent is None:
                source_byte = source_pixel * 2
                destination_byte = destination_pixel * 2
                byte_count = draw_width * 2

                self.buffer[
                    destination_byte:
                    destination_byte + byte_count
                ] = source[
                    source_byte:
                    source_byte + byte_count
                ]

                continue

            for column in range(draw_width):
                source_byte = (
                    source_pixel + column
                ) * 2

                colour = self._read_rgb565(
                    source,
                    source_byte,
                    big_endian
                )

                if (
                    transparent is not None
                    and colour == (transparent & 0xFFFF)
                ):
                    continue

                destination_byte = (
                    destination_pixel + column
                ) * 2

                self._write_colour(
                    self.buffer,
                    destination_byte,
                    colour
                )

        return draw_width, draw_height

    def draw(
        self,
        target,
        x,
        y,
        source_x=0,
        source_y=0,
        width=None,
        height=None,
        transparent=None,
        use_sprite_transparency=True
    ):
        """
        Draw all or part of the sprite onto a compatible target.
        """
        source_x = int(source_x)
        source_y = int(source_y)

        if width is None:
            width = self.width - source_x

        if height is None:
            height = self.height - source_y

        width = int(width)
        height = int(height)

        if source_x < 0:
            x -= source_x
            width += source_x
            source_x = 0

        if source_y < 0:
            y -= source_y
            height += source_y
            source_y = 0

        if source_x + width > self.width:
            width = self.width - source_x

        if source_y + height > self.height:
            height = self.height - source_y

        if width <= 0 or height <= 0:
            return 0, 0

        colour_key = transparent

        if (
            colour_key is None
            and use_sprite_transparency
        ):
            colour_key = self.transparent

        return target.blit_rgb565(
            self.buffer,
            x,
            y,
            width,
            height,
            stride=self.width,
            offset=(source_y * self.width) + source_x,
            byteorder="big",
            transparent=colour_key
        )

    def subsprite(
        self,
        x,
        y,
        width,
        height,
        transparent=None
    ):
        """Return a copied rectangular region as a new Sprite."""
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            raise ValueError("subsprite dimensions must be positive")

        new_sprite = Sprite(
            width,
            height,
            transparent=(
                self.transparent
                if transparent is None
                else transparent
            )
        )

        new_sprite.blit_rgb565(
            self.buffer,
            -x,
            -y,
            self.width,
            self.height,
            stride=self.width,
            byteorder="big"
        )

        return new_sprite

    def save_raw(self, path, byteorder="big"):
        """
        Save the complete sprite as headerless RGB565 data.
        """
        big_endian = self._normalise_byteorder(byteorder)

        with open(path, "wb") as file:
            if big_endian:
                file.write(self.buffer)
                return

            # Convert and write in small chunks rather than allocating
            # another full sprite-sized buffer.
            chunk = bytearray(256)
            chunk_view = memoryview(chunk)
            source_index = 0

            while source_index < len(self.buffer):
                byte_count = min(
                    len(chunk),
                    len(self.buffer) - source_index
                )

                # Keep the chunk length even.
                byte_count &= ~1

                for index in range(0, byte_count, 2):
                    chunk[index] = (
                        self.buffer[source_index + index + 1]
                    )
                    chunk[index + 1] = (
                        self.buffer[source_index + index]
                    )

                file.write(chunk_view[:byte_count])
                source_index += byte_count

    @classmethod
    def from_raw(
        cls,
        path,
        width,
        height,
        byteorder="big",
        transparent=None
    ):
        """
        Load a complete headerless RGB565 file without duplicating it.
        """
        width = int(width)
        height = int(height)
        required_bytes = width * height * 2

        sprite = cls(
            width,
            height,
            transparent=transparent
        )

        with open(path, "rb") as file:
            destination = memoryview(sprite.buffer)
            total_read = 0

            while total_read < required_bytes:
                count = file.readinto(destination[total_read:])

                if not count:
                    break

                total_read += count

        if total_read != required_bytes:
            raise ValueError("raw file is smaller than expected")

        big_endian = cls._normalise_byteorder(byteorder)

        if not big_endian:
            buffer_data = sprite.buffer

            for index in range(0, required_bytes, 2):
                buffer_data[index], buffer_data[index + 1] = (
                    buffer_data[index + 1],
                    buffer_data[index]
                )

        return sprite
