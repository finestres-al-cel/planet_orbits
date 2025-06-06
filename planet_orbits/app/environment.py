"""Definition of environment-like variables"""
import os

from PyQt6.QtGui import QPalette, QColor

# paths
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BUTTONS_PATH = f"{THIS_DIR}/button_plots/"

# window properties
WIDTH = 1600
HEIGHT = 800
ICON_SIZE = 30

# font properties
TITLE_FONT_SIZE = 18
MENU_FONT_SIZE = 14

# Set colors based on the detected mode
def get_background_color(palette):
    """
    Get a contrasting background color based on the system's background color.
    
    Arguments
    ---------
    palette: QPalette
        The application's palette.

    Returns
    -------
    QColor
        A contrasting background color.
    """
    # Check if the system background is dark
    is_dark_mode = palette.color(QPalette.ColorRole.Window).value() < 128

    # Return a contrasting color
    if is_dark_mode:
        return QColor("white")  # Light color for dark backgrounds
    else:
        return QColor("black")  # Dark color for light backgrounds


def get_colors(palette):
    """
    Detect system color scheme and return background and text colors.
    
    Arguments
    ---------
    palette: QPalette
    The application's palette.

    Returns
    -------
    colors: (str, str)
    Tuple with background and text colors.
    """
    # Check if the background is dark
    is_dark_mode = palette.color(QPalette.ColorRole.Window).value() < 128  
    if is_dark_mode:
        return "black", "white"
    else:
        return "white", "black"