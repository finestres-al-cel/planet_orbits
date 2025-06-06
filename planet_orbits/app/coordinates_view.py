"""Defines the CoordinatesView class."""
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QLabel, QDoubleSpinBox
)

class CoordinatesView(QWidget):
    """Coordinates View

    This class is responsible for displaying the coordinates of planets
    in a table format. 

    Attributes
    ----------
    tableView: QTableView
    The table view widget that displays the planet coordinates.
    
    model: PlanetCoordinatesModel
    The model that provides data to the table view.
    """
    def __init__(self, planetCoordinates, parent=None):
        """Initialize the CoordinatesView.

        Arguments
        ---------
        parent: QWidget - default: None
        The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Planet Coordinates")

        self.planetCoordinates = planetCoordinates
        self.planetSelector = None
        
        self.ax = None

        # Main layout
        self.mainLayout = QHBoxLayout(self)

        # Plot area
        self.plotCanvas = FigureCanvas(Figure(figsize=(8, 8)))
        self._setupPlot()
        self.mainLayout.addWidget(self.plotCanvas, stretch=3)

        # Options area
        self.a_planet_label = None
        self.a_planet_box = None
        self.e_planet_label = None
        self.e_planet_box = None
        self.e_earth_label = None
        self.e_earth_box = None
        self.optionsLayout = None
        self.planetSelector = None
        self.optionsBox = self._createOptionsBox()
        self.mainLayout.addWidget(self.optionsBox, stretch=1)

        self.setLayout(self.mainLayout)

    def _createOptionsBox(self):
        """Create the options box for modeling."""
        optionsBox = QGroupBox("Modeling Options")
        #layout = QVBoxLayout()
        self.optionsLayout = QVBoxLayout()

        # Planet selector
        self.planetSelector = QComboBox()
        self.planetSelector.addItem("Select a planet")
        self.planetSelector.addItems(
            ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", 
             "Uranus", "Neptune"])  
        self.planetSelector.currentTextChanged.connect(self._onPlanetSelected)
        self.optionsLayout.addWidget(self.planetSelector)

        # Prepare parameter widgets but do not add yet,
        # they will be added when a planet is selected
        # a_planet input
        self.a_planet_label = QLabel("semi-major axis (planet) [AU]")
        self.a_planet_box = QDoubleSpinBox()
        self.a_planet_box.setDecimals(3)
        self.a_planet_box.setRange(0.1, 100.0)
        self.a_planet_box.setSingleStep(0.01)
        self.a_planet_box.valueChanged.connect(self._onParamsChanged)

        # e_planet input
        self.e_planet_label = QLabel("eccentricity (planet)")
        self.e_planet_box = QDoubleSpinBox()
        self.e_planet_box.setDecimals(3)
        self.e_planet_box.setRange(0.0, 1.0)
        self.e_planet_box.setSingleStep(0.01)
        self.e_planet_box.valueChanged.connect(self._onParamsChanged)

        # e_earth input
        self.e_earth_label = QLabel("eccentricity (Earth)")
        self.e_earth_box = QDoubleSpinBox()
        self.e_earth_box.setDecimals(3)
        self.e_earth_box.setRange(0.0, 1.0)
        self.e_earth_box.setSingleStep(0.01)
        self.e_earth_box.valueChanged.connect(self._onParamsChanged)

        #layout.addStretch(1)  
        #optionsBox.setLayout(layout)
        self.optionsLayout.addStretch(1) # Push buttons to the top    
        optionsBox.setLayout(self.optionsLayout)

        return optionsBox
    
    def _loadData(self):
        """Load data and update the plot."""
        # clear previous plot
        if self.ax is not None:
            self._resetPlot()
        else:
            self._setupPlot()
        
        self.ax.clear()
        self.ax.set_title("Planet Positions")
        self.ax.set_xlabel("X [AU]")
        self.ax.set_ylabel("Y [AU]")
        self.ax.grid(True)
        self.ax.axis("equal")

        # Load data from the planetCoordinates object
        if self.planetCoordinates.selected_planet is not None:
            
            # Plot Sun
            sun_x = self.planetCoordinates.sun_x
            sun_y = self.planetCoordinates.sun_y
            self.ax.plot(sun_x, sun_y, 'yo', label="Sun")

            # Plot Earth
            earth_x = np.concatenate(list(self.planetCoordinates.earth_x.values()))
            earth_y = np.concatenate(list(self.planetCoordinates.earth_y.values()))
            self.ax.plot(earth_x, earth_y, 'bo', label="Earth")

            # Plot Target planet
            planet_x = np.concatenate(list(self.planetCoordinates.planet_x.values()))
            planet_y = np.concatenate(list(self.planetCoordinates.planet_y.values()))
            self.ax.plot(planet_x, planet_y, 'ro', label=self.planetCoordinates.selected_planet)

            # Plot Earth's orbit
            model_x_earth = self.planetCoordinates.model_x_earth
            model_y_earth = self.planetCoordinates.model_y_earth
            self.ax.plot(model_x_earth, model_y_earth, 'b-', label="Earth's Orbit")

            # Plot Target planet's orbit
            model_x_planet = self.planetCoordinates.model_x_planet
            model_y_planet = self.planetCoordinates.model_y_planet
            self.ax.plot(model_x_planet, model_y_planet, 'r-', label=f"{self.planetCoordinates.selected_planet}'s Orbit")

            # Add legend
            self.ax.legend()
        
        self.plotCanvas.draw()

    def _onParamsChanged(self):
        """Update model parameters and refresh plot when any parameter changes."""
        self.planetCoordinates.a_planet = self.a_planet_box.value()
        self.planetCoordinates.e_planet = self.e_planet_box.value()
        self.planetCoordinates.e_earth = self.e_earth_box.value()
        # Recompute positions for the current planet and date
        if self.planetCoordinates.selected_planet is not None:
            self.planetCoordinates.set_planet_positions(self.planetCoordinates.dates[0])
            self.planetCoordinates.set_model_positions()
            self._loadData()

    def _onPlanetSelected(self, selected_planet):
        """Handle planet selection from the dropdown menu."""
        #self.planetCoordinates.set_selected_planet(selected_planet)
        #self._loadData()  # Reload the data and update the plot
        for widget in [self.a_planet_label, self.a_planet_box,
                    self.e_planet_label, self.e_planet_box,
                    self.e_earth_label, self.e_earth_box]:
            self.optionsLayout.removeWidget(widget)
            widget.setParent(None)

        if selected_planet == "Select a planet":
            self.planetCoordinates.set_selected_planet(None)
            self._loadData()
            return

        # Set default values
        self.planetCoordinates.set_selected_planet(selected_planet)
        self.a_planet_box.setValue(self.planetCoordinates.a_planet)
        self.e_planet_box.setValue(self.planetCoordinates.e_planet)
        self.e_earth_box.setValue(self.planetCoordinates.e_earth)

        # Update labels
        self.a_planet_label = QLabel(
            f"semi-major axis ({self.planetCoordinates.selected_planet}) [AU]")
        self.e_planet_label = QLabel(
            f"eccentricity ({self.planetCoordinates.selected_planet})")
        
        # Add parameter widgets
        self.optionsLayout.insertWidget(1, self.a_planet_label)
        self.optionsLayout.insertWidget(2, self.a_planet_box)
        self.optionsLayout.insertWidget(3, self.e_planet_label)
        self.optionsLayout.insertWidget(4, self.e_planet_box)
        self.optionsLayout.insertWidget(5, self.e_earth_label)
        self.optionsLayout.insertWidget(6, self.e_earth_box)

        self._loadData()        

    def _resetPlot(self):
        """Reset the plot to its initial state."""
        self.ax.clear()
        self.ax.set_title("Planet Positions")
        self.ax.set_xlabel("X (AU)")
        self.ax.set_ylabel("Y (AU)")
        self.ax.grid(True)
        self.ax.axis("equal")

    def _runModel(self):
        """Run the selected model."""
        print("Running model...")

    def _setupPlot(self):
        """Set up the plot area."""
        self.ax = self.plotCanvas.figure.add_subplot(111)
        self.ax.set_title("Planet Positions")
        self.ax.set_xlabel("X (AU)")
        self.ax.set_ylabel("Y (AU)")
        self.ax.grid(True)
        self.ax.axis("equal")