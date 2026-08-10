"""
layout.py
=========

Small bounded text-layout helpers for the fixed 8 x 8 font.

Version: 0.7.0

This functionality is kept outside graphics.py so the already-large
graphics module remains close to the physically tested Version 0.6.0
size. Smaller modules reduce MicroPython source-compilation peak memory
on the Pyboard v1.1.
"""

from font8 import FONT_WIDTH, FONT_HEIGHT


def _normalise_scale(scale):
    scale = int(scale)

    if scale < 1:
        return 1

    return scale


def wrap_lines(
    text,
    maximum_characters,
    maximum_lines=None,
    tab_size=4
):
    """
    Convert text into word-wrapped lines.

    Long individual words are divided when they cannot fit.
    """
    text = str(text).replace(
        "\t",
        " " * max(1, int(tab_size))
    )

    maximum_characters = max(
        1,
        int(maximum_characters)
    )

    if maximum_lines is not None:
        maximum_lines = max(
            0,
            int(maximum_lines)
        )

    lines = []
    truncated = False
    paragraphs = text.split("\n")

    for paragraph_index, paragraph in enumerate(paragraphs):
        words = paragraph.split()
        current = ""

        if not words:
            lines.append("")

            if (
                maximum_lines is not None
                and len(lines) >= maximum_lines
            ):
                truncated = (
                    paragraph_index
                    < len(paragraphs) - 1
                )
                break

            continue

        for word_index, word in enumerate(words):
            while len(word) > maximum_characters:
                if current:
                    lines.append(current)
                    current = ""

                    if (
                        maximum_lines is not None
                        and len(lines) >= maximum_lines
                    ):
                        truncated = True
                        break

                lines.append(
                    word[:maximum_characters]
                )
                word = word[maximum_characters:]

                if (
                    maximum_lines is not None
                    and len(lines) >= maximum_lines
                ):
                    truncated = bool(word)
                    break

            if truncated:
                break

            if not word:
                continue

            candidate = (
                word
                if not current
                else current + " " + word
            )

            if len(candidate) <= maximum_characters:
                current = candidate
            else:
                lines.append(current)
                current = word

                if (
                    maximum_lines is not None
                    and len(lines) >= maximum_lines
                ):
                    truncated = True
                    break

        if truncated:
            break

        if current:
            lines.append(current)

        if (
            maximum_lines is not None
            and len(lines) >= maximum_lines
        ):
            if paragraph_index < len(paragraphs) - 1:
                truncated = True
            break

    if maximum_lines is not None and len(lines) > maximum_lines:
        lines = lines[:maximum_lines]
        truncated = True

    return lines, truncated


def text_box(
    gfx,
    text,
    x,
    y,
    width,
    height,
    colour,
    background=None,
    scale=1,
    spacing=1,
    line_spacing=1,
    align="left",
    tab_size=4,
    ellipsis=False
):
    """
    Draw word-wrapped text inside a bounded rectangle.

    Returns:
        (lines_drawn, truncated, final_y)
    """
    x = int(x)
    y = int(y)
    width = int(width)
    height = int(height)

    if width <= 0 or height <= 0:
        return 0, bool(str(text)), y

    scale = _normalise_scale(scale)
    spacing = max(0, int(spacing))
    line_spacing = max(0, int(line_spacing))

    glyph_width = FONT_WIDTH * scale
    glyph_height = FONT_HEIGHT * scale
    spacing_width = spacing * scale

    character_advance = glyph_width + spacing_width
    line_advance = (
        FONT_HEIGHT + line_spacing
    ) * scale

    maximum_characters = (
        width + spacing_width
    ) // character_advance

    if maximum_characters < 1 or height < glyph_height:
        return 0, bool(str(text)), y

    maximum_lines = (
        (height - glyph_height)
        // line_advance
    ) + 1

    lines, truncated = wrap_lines(
        text,
        maximum_characters,
        maximum_lines=maximum_lines,
        tab_size=tab_size
    )

    if truncated and ellipsis and lines:
        if maximum_characters >= 3:
            lines[-1] = (
                lines[-1][:maximum_characters - 3]
                + "..."
            )

    align = str(align).lower()

    if align == "center":
        align = "centre"

    if align not in ("left", "centre", "right"):
        raise ValueError(
            "align must be left, centre, center, or right"
        )

    cursor_y = y

    for line in lines:
        line_width = gfx.text_width(
            line,
            scale=scale,
            spacing=spacing,
            tab_size=tab_size
        )

        if align == "centre":
            line_x = x + max(
                0,
                (width - line_width) // 2
            )
        elif align == "right":
            line_x = x + max(
                0,
                width - line_width
            )
        else:
            line_x = x

        gfx.text(
            line,
            line_x,
            cursor_y,
            colour,
            background=background,
            scale=scale,
            spacing=spacing,
            line_spacing=line_spacing,
            wrap=False,
            tab_size=tab_size
        )

        cursor_y += line_advance

    return len(lines), truncated, cursor_y
