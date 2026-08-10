#!/usr/bin/env python3
"""
image_converter.py
==================

Desktop image converter for ILI9488 library Version 0.7.0.

Requires Pillow:

    python -m pip install Pillow

Examples
--------

Create both outputs at the original size:

    python image_converter.py picture.png --bmp picture.bmp \
        --raw picture.raw

Resize to 120 x 80 first:

    python image_converter.py picture.jpg --size 120 80 \
        --bmp picture.bmp --raw picture.raw

The BMP output is uncompressed 24-bit RGB.
The RAW output is headerless big-endian RGB565.
"""

import argparse
from pathlib import Path

from PIL import Image


def rgb565(red, green, blue):
    return (
        ((red & 0xF8) << 8)
        | ((green & 0xFC) << 3)
        | (blue >> 3)
    )


def save_rgb565_raw(image, path):
    image = image.convert("RGB")
    output = bytearray(image.width * image.height * 2)
    output_index = 0

    for red, green, blue in image.getdata():
        colour = rgb565(red, green, blue)

        output[output_index] = (colour >> 8) & 0xFF
        output[output_index + 1] = colour & 0xFF
        output_index += 2

    Path(path).write_bytes(output)


def main():
    parser = argparse.ArgumentParser(
        description="Convert an image for the MicroPython ILI9488 library."
    )

    parser.add_argument("input", help="source image path")
    parser.add_argument("--bmp", help="output uncompressed 24-bit BMP")
    parser.add_argument("--raw", help="output big-endian RGB565 RAW")
    parser.add_argument(
        "--size",
        nargs=2,
        type=int,
        metavar=("WIDTH", "HEIGHT"),
        help="resize before conversion"
    )

    arguments = parser.parse_args()

    if not arguments.bmp and not arguments.raw:
        parser.error("at least one of --bmp or --raw is required")

    image = Image.open(arguments.input).convert("RGB")

    if arguments.size:
        width, height = arguments.size

        if width <= 0 or height <= 0:
            parser.error("resize dimensions must be positive")

        image = image.resize(
            (width, height),
            Image.Resampling.LANCZOS
        )

    if arguments.bmp:
        image.save(
            arguments.bmp,
            format="BMP"
        )

        print(
            "Wrote BMP:",
            arguments.bmp,
            "{}x{}".format(image.width, image.height)
        )

    if arguments.raw:
        save_rgb565_raw(
            image,
            arguments.raw
        )

        print(
            "Wrote RAW:",
            arguments.raw,
            "{}x{}".format(image.width, image.height)
        )


if __name__ == "__main__":
    main()
