"""
bitmap.py
=========

Memory-conscious image-file rendering for the ILI9488 library.

Version: 0.7.1

Supported BMP files
-------------------
- Uncompressed 24-bit BMP
- Uncompressed 32-bit BMP
- Uncompressed 16-bit RGB555 BMP
- 16-bit BI_BITFIELDS BMP, including RGB565

Supported raw files
-------------------
- Headerless RGB565
- Big-endian or little-endian
- Caller supplies the full image width and height

All functions read and convert one visible row at a time. A full image
is therefore not loaded into RAM.

The destination may be either:

- Display from display.py
- Sprite from sprite.py

Both provide the required blit_rgb565() method.
"""

try:
    from sprite import Sprite
except ImportError:
    Sprite = None


class BitmapError(Exception):
    """Raised for unsupported or invalid bitmap files."""


def _read_exact(file, size):
    data = file.read(size)

    if len(data) != size:
        raise BitmapError("unexpected end of file")

    return data


def _u16(data, offset):
    return (
        data[offset]
        | (data[offset + 1] << 8)
    )


def _u32(data, offset):
    return (
        data[offset]
        | (data[offset + 1] << 8)
        | (data[offset + 2] << 16)
        | (data[offset + 3] << 24)
    )


def _s32(data, offset):
    value = _u32(data, offset)

    if value & 0x80000000:
        value -= 0x100000000

    return value


def _mask_details(mask):
    if mask == 0:
        return 0, 0

    shift = 0

    while not (mask & 1):
        mask >>= 1
        shift += 1

    return shift, mask


def _masked_component(value, details):
    shift, maximum = details

    if maximum == 0:
        return 0

    component = (value >> shift) & maximum

    return (component * 255) // maximum


def _rgb888_to_rgb565(red, green, blue):
    return (
        ((red & 0xF8) << 8)
        | ((green & 0xFC) << 3)
        | (blue >> 3)
    )


def _read_bmp_header(file):
    file.seek(0)
    file_header = _read_exact(file, 14)

    if file_header[0:2] != b"BM":
        raise BitmapError("file is not a Windows BMP")

    pixel_offset = _u32(file_header, 10)

    dib_size_data = _read_exact(file, 4)
    dib_size = _u32(dib_size_data, 0)

    if dib_size < 40:
        raise BitmapError("unsupported BMP information header")

    dib = dib_size_data + _read_exact(file, dib_size - 4)

    width = _s32(dib, 4)
    signed_height = _s32(dib, 8)
    planes = _u16(dib, 12)
    bits_per_pixel = _u16(dib, 14)
    compression = _u32(dib, 16)

    if width <= 0 or signed_height == 0:
        raise BitmapError("invalid BMP dimensions")

    if planes != 1:
        raise BitmapError("invalid BMP plane count")

    height = abs(signed_height)
    top_down = signed_height < 0

    if bits_per_pixel in (24, 32):
        if compression != 0:
            raise BitmapError(
                "24/32-bit BMP must be uncompressed"
            )

        red_mask = None
        green_mask = None
        blue_mask = None

    elif bits_per_pixel == 16:
        if compression == 0:
            # BI_RGB 16-bit BMP conventionally uses RGB555.
            red_mask = 0x7C00
            green_mask = 0x03E0
            blue_mask = 0x001F

        elif compression == 3:
            if dib_size >= 52:
                red_mask = _u32(dib, 40)
                green_mask = _u32(dib, 44)
                blue_mask = _u32(dib, 48)
            else:
                current_position = file.tell()
                file.seek(14 + dib_size)
                masks = _read_exact(file, 12)
                file.seek(current_position)

                red_mask = _u32(masks, 0)
                green_mask = _u32(masks, 4)
                blue_mask = _u32(masks, 8)

        else:
            raise BitmapError(
                "unsupported 16-bit BMP compression"
            )

    else:
        raise BitmapError(
            "only 16, 24 and 32-bit BMP files are supported"
        )

    row_stride = (
        ((width * bits_per_pixel) + 31) // 32
    ) * 4

    header = {
        "width": width,
        "height": height,
        "top_down": top_down,
        "bits_per_pixel": bits_per_pixel,
        "compression": compression,
        "pixel_offset": pixel_offset,
        "row_stride": row_stride,
        "bytes_per_pixel": bits_per_pixel // 8,
        "red_mask": red_mask,
        "green_mask": green_mask,
        "blue_mask": blue_mask
    }

    if bits_per_pixel == 16:
        header["red_details"] = _mask_details(red_mask)
        header["green_details"] = _mask_details(green_mask)
        header["blue_details"] = _mask_details(blue_mask)

    return header


def bmp_info(path):
    """
    Return a dictionary describing a supported BMP file.
    """
    with open(path, "rb") as file:
        return _read_bmp_header(file)


def _clip_region(
    target,
    image_width,
    image_height,
    x,
    y,
    source_x,
    source_y,
    width,
    height
):
    x = int(x)
    y = int(y)
    source_x = int(source_x)
    source_y = int(source_y)

    if width is None:
        width = image_width - source_x

    if height is None:
        height = image_height - source_y

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

    if source_x + width > image_width:
        width = image_width - source_x

    if source_y + height > image_height:
        height = image_height - source_y

    if x < 0:
        source_x -= x
        width += x
        x = 0

    if y < 0:
        source_y -= y
        height += y
        y = 0

    if x + width > target.width:
        width = target.width - x

    if y + height > target.height:
        height = target.height - y

    if width <= 0 or height <= 0:
        return None

    return (
        x,
        y,
        source_x,
        source_y,
        width,
        height
    )


def _convert_bmp_row(source, header, width):
    bits_per_pixel = header["bits_per_pixel"]
    output = bytearray(width * 2)

    if bits_per_pixel == 24:
        for pixel in range(width):
            source_index = pixel * 3

            blue = source[source_index]
            green = source[source_index + 1]
            red = source[source_index + 2]

            colour = _rgb888_to_rgb565(
                red,
                green,
                blue
            )

            output_index = pixel * 2
            output[output_index] = (colour >> 8) & 0xFF
            output[output_index + 1] = colour & 0xFF

    elif bits_per_pixel == 32:
        for pixel in range(width):
            source_index = pixel * 4

            blue = source[source_index]
            green = source[source_index + 1]
            red = source[source_index + 2]

            colour = _rgb888_to_rgb565(
                red,
                green,
                blue
            )

            output_index = pixel * 2
            output[output_index] = (colour >> 8) & 0xFF
            output[output_index + 1] = colour & 0xFF

    else:
        red_details = header["red_details"]
        green_details = header["green_details"]
        blue_details = header["blue_details"]

        for pixel in range(width):
            source_index = pixel * 2

            value = (
                source[source_index]
                | (source[source_index + 1] << 8)
            )

            red = _masked_component(value, red_details)
            green = _masked_component(value, green_details)
            blue = _masked_component(value, blue_details)

            colour = _rgb888_to_rgb565(
                red,
                green,
                blue
            )

            output_index = pixel * 2
            output[output_index] = (colour >> 8) & 0xFF
            output[output_index + 1] = colour & 0xFF

    return output


def draw_bmp(
    target,
    path,
    x,
    y,
    source_x=0,
    source_y=0,
    width=None,
    height=None,
    transparent=None
):
    """
    Draw all or part of a supported BMP file.

    Returns the visible width and height.
    """
    with open(path, "rb") as file:
        header = _read_bmp_header(file)

        clipped = _clip_region(
            target,
            header["width"],
            header["height"],
            x,
            y,
            source_x,
            source_y,
            width,
            height
        )

        if clipped is None:
            return 0, 0

        (
            x,
            y,
            source_x,
            source_y,
            width,
            height
        ) = clipped

        bytes_per_pixel = header["bytes_per_pixel"]

        for output_row in range(height):
            image_y = source_y + output_row

            if header["top_down"]:
                file_row = image_y
            else:
                file_row = (
                    header["height"] - 1 - image_y
                )

            row_position = (
                header["pixel_offset"]
                + (file_row * header["row_stride"])
                + (source_x * bytes_per_pixel)
            )

            file.seek(row_position)

            source_row = _read_exact(
                file,
                width * bytes_per_pixel
            )

            rgb565_row = _convert_bmp_row(
                source_row,
                header,
                width
            )

            target.blit_rgb565(
                rgb565_row,
                x,
                y + output_row,
                width,
                1,
                byteorder="big",
                transparent=transparent
            )

    return width, height


def draw_raw(
    target,
    path,
    image_width,
    image_height,
    x,
    y,
    source_x=0,
    source_y=0,
    width=None,
    height=None,
    byteorder="big",
    transparent=None
):
    """
    Draw all or part of a headerless RGB565 file.

    image_width and image_height describe the complete raw image.
    """
    image_width = int(image_width)
    image_height = int(image_height)

    if image_width <= 0 or image_height <= 0:
        raise ValueError("raw image dimensions must be positive")

    clipped = _clip_region(
        target,
        image_width,
        image_height,
        x,
        y,
        source_x,
        source_y,
        width,
        height
    )

    if clipped is None:
        return 0, 0

    (
        x,
        y,
        source_x,
        source_y,
        width,
        height
    ) = clipped

    with open(path, "rb") as file:
        for output_row in range(height):
            image_y = source_y + output_row

            row_position = (
                ((image_y * image_width) + source_x)
                * 2
            )

            file.seek(row_position)
            row_data = file.read(width * 2)

            if len(row_data) != width * 2:
                raise BitmapError(
                    "raw file is smaller than its stated dimensions"
                )

            target.blit_rgb565(
                row_data,
                x,
                y + output_row,
                width,
                1,
                byteorder=byteorder,
                transparent=transparent
            )

    return width, height


def load_bmp_sprite(
    path,
    source_x=0,
    source_y=0,
    width=None,
    height=None,
    transparent=None
):
    """
    Load a BMP region into a new Sprite.
    """
    if Sprite is None:
        raise BitmapError("sprite.py is unavailable")

    information = bmp_info(path)

    if width is None:
        width = information["width"] - int(source_x)

    if height is None:
        height = information["height"] - int(source_y)

    width = int(width)
    height = int(height)

    if width <= 0 or height <= 0:
        raise ValueError("sprite dimensions must be positive")

    sprite = Sprite(
        width,
        height,
        transparent=transparent
    )

    draw_bmp(
        sprite,
        path,
        0,
        0,
        source_x=source_x,
        source_y=source_y,
        width=width,
        height=height
    )

    return sprite


def load_raw_sprite(
    path,
    width,
    height,
    byteorder="big",
    transparent=None
):
    """
    Load a complete raw RGB565 file into a new Sprite.
    """
    if Sprite is None:
        raise BitmapError("sprite.py is unavailable")

    return Sprite.from_raw(
        path,
        width,
        height,
        byteorder=byteorder,
        transparent=transparent
    )
