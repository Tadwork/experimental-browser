"""Module for caching fonts."""
import tkinter.font as tkfont

FONTS = {}

def get_font(family: str, size: int, weight: str, slant: str):
    """_summary_

    Args:
        family (str): The font family
        size (int): The font size 
        weight (str): "normal" or "bold"
        slant (str): "roman" or "italic"

    Returns:
        font: a font object
    """
    key = (family, size, weight, slant)
    if key not in FONTS:
        font = tkfont.Font(
            family=family,
            size=size,
            weight=weight,
            slant=slant,
        )
        FONTS[key] = font
    return FONTS[key]
