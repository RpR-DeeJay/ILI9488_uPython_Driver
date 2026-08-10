"""RGB565 colours and helpers. Version 0.7.1."""

def rgb565(red, green, blue):
    red = max(0, min(255, int(red)))
    green = max(0, min(255, int(green)))
    blue = max(0, min(255, int(blue)))
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)

def rgb565_to_rgb888(colour):
    colour &= 0xFFFF
    r5 = (colour >> 11) & 0x1F
    g6 = (colour >> 5) & 0x3F
    b5 = colour & 0x1F
    return ((r5 << 3) | (r5 >> 2), (g6 << 2) | (g6 >> 4), (b5 << 3) | (b5 >> 2))

BLACK=0x0000; WHITE=0xFFFF; RED=0xF800; GREEN=0x07E0; BLUE=0x001F
YELLOW=0xFFE0; CYAN=0x07FF; MAGENTA=0xF81F
DARK_RED=rgb565(128,0,0); DARK_GREEN=rgb565(0,128,0); DARK_BLUE=rgb565(0,0,128)
ORANGE=rgb565(255,165,0); PURPLE=rgb565(128,0,128); PINK=rgb565(255,105,180); BROWN=rgb565(165,42,42)
NAVY=rgb565(0,0,96); TEAL=rgb565(0,128,128); LIME=rgb565(128,255,0)
GREY=rgb565(128,128,128); DARK_GREY=rgb565(64,64,64); LIGHT_GREY=rgb565(192,192,192)
