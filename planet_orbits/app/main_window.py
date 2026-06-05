"""planet_orbits main window"""
import os

from PyQt6.QtCore import QSize, Qt, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QToolBar,
    QWidget,
)

from planet_orbits.app.coordinates_view import CoordinatesView
from planet_orbits.app.environment import (
    HEIGHT, ICON_SIZE, MENU_FONT_SIZE, TITLE_FONT_SIZE, WIDTH, 
    get_colors,
)
from planet_orbits.app.error_dialog import ErrorDialog
from planet_orbits.app.load_actions import (
    loadFileMenuActions,
)
from planet_orbits.app.success_dialog import SuccessDialog
from planet_orbits.errors import PlanetOrbitalSolverError
from planet_orbits.planet_orbital_solver import PlanetOrbitalSolver

class MainWindow(QMainWindow):
    """Main Window

    Methods
    -------
    (see QMainWindow)
    __init__
    _createToolBar
    _createMenuBar
    _createStatusBar
    _loadActions

    Attributes
    ----------
    (see QMainWindow)

    centralWidget: QtWidget
    Central widget
    """
    def __init__(self):
        """Initialize class instance """
        super().__init__()

        self.setWindowTitle("Planet Orbits")
        self.setGeometry(0, 0, WIDTH, HEIGHT)

        self.centralWidget = QLabel("Welcome to Planet Orbits")

        # Dynamically setup color scheme
        palette = self.palette()
        background_color, text_color = get_colors(palette)
        self.centralWidget.setStyleSheet(
            f"background-color: {background_color}; "
            f"color: {text_color}; "
            f" font-size: {TITLE_FONT_SIZE}px; ")
        self.centralWidget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(self.centralWidget)

        """self.centralWidget.setWordWrap(True)
        
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background-color: white;")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "planet.png")))
        self.setStyleSheet("background-color: white;")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowModal, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, False)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnBottom, False)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnBottom, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, False)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnBottom, False)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnBottom, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, False)"""

        # Load actions
        self.fileActions = loadFileMenuActions(self)

        # Create menues
        self._createToolBar()
        self._createStatusBar()
        self._createMenuBar()

        # define variables
        self.planetOrbitalSolver = None
        self.coordinatesView = None

    def _createToolBar(self):
        """Create tool bars"""
        fileToolBar = QToolBar("File toolbar")
        #fileToolBar.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        fileToolBar.setFont(QFont("", MENU_FONT_SIZE))
        for menuAction in self.fileActions:
            fileToolBar.addAction(menuAction)
            fileToolBar.addSeparator()
        self.addToolBar(fileToolBar)

    def _createMenuBar(self):
        """Create menu bars"""
        menu = self.menuBar()

        fileMenu = menu.addMenu("&File")
        for menuAction in self.fileActions:
            fileMenu.addAction(menuAction)
            fileMenu.addSeparator()

    def _createStatusBar(self):
        """Create status bar"""
        self.setStatusBar(QStatusBar(self))

    @pyqtSlot()
    def openFile(self):
        """Open dialog to select and open file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "${HOME}",
            "CSV (*.csv);; Data (*dat);; Text (*txt);; All files (*)",
        )

        if filename:
            try:
                # Initialize the planetOrbitalSolver class and load the data
                self.planetOrbitalSolver = PlanetOrbitalSolver(filename)
                
            except Exception as e:
                # Show error dialog
                errorDialog = ErrorDialog(str(e))
                errorDialog.exec()
                raise e

            try:
                self.coordinatesView = CoordinatesView(self.planetOrbitalSolver)
                self.setCentralWidget(self.coordinatesView)

            except PlanetOrbitalSolverError as error:
                errorDialog = ErrorDialog(
                    "An error occurred when displaying data:\n" + str(error))
                errorDialog.exec()