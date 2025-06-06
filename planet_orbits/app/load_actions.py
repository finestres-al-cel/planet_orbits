""" Functions to load Actions"""
import os

from PyQt6.QtGui import QAction, QIcon, QPainter, QPixmap

from planet_orbits.app.environment import (
    BUTTONS_PATH, ICON_SIZE,
    get_background_color
)

def createIconWithBackground(icon_path, bg_color):
    """Create an icon with a visible background"""
    pixmap = QPixmap(ICON_SIZE, ICON_SIZE)
    pixmap.fill(bg_color)  # Fill the background with the specified color

    painter = QPainter(pixmap)
    icon = QPixmap(icon_path)
    icon = icon.scaled(ICON_SIZE - 4, ICON_SIZE - 4)  # Scale the icon to fit within the background
    painter.drawPixmap(2, 2, icon)  # Draw the icon with padding
    painter.end()

    return QIcon(pixmap)

def loadFileMenuActions(window):
    """Load file menu actions

    Arguments
    ---------
    window: MainWindow
    Window where the actions will act

    Returns
    -------
    menuAction: list of QAction
    List of actions in the file menu
    """
    menuActions = []

    load_spectrum_option = QAction(
        createIconWithBackground(
            os.path.join(BUTTONS_PATH, "load_file.png"),
            get_background_color(window.palette()),
        ),
        "&Load File",
        window)
    load_spectrum_option.setStatusTip("Load File")
    load_spectrum_option.triggered.connect(window.openFile)
    menuActions.append(load_spectrum_option)

    return menuActions
