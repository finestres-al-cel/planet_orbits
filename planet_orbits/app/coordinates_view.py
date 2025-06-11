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
        self.planet_a_label = None
        self.planet_a_box = None
        self.planet_e_label = None
        self.planet_e_box = None
        self.planet_phase_label = None
        self.planet_phase_box = None
        self.earth_e_label = None
        self.earth_e_box = None
        self.earth_phase_label = None
        self.earth_phase_box = None
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
        # planet semi-major axis input
        self.planet_a_label = QLabel("semi-major axis (planet) [AU]")
        self.planet_a_box = QDoubleSpinBox()
        self.planet_a_box.setDecimals(3)
        self.planet_a_box.setRange(0.1, 100.0)
        self.planet_a_box.setSingleStep(0.01)
        self.planet_a_box.valueChanged.connect(self._onParamsChanged)

        # planet eccentricity input
        self.planet_e_label = QLabel("eccentricity (planet)")
        self.planet_e_box = QDoubleSpinBox()
        self.planet_e_box.setDecimals(3)
        self.planet_e_box.setRange(0.0, 1.0)
        self.planet_e_box.setSingleStep(0.01)
        self.planet_e_box.valueChanged.connect(self._onParamsChanged)

        # planet phase input
        self.planet_phase_label = QLabel("phase (planet) [deg]")
        self.planet_phase_box = QDoubleSpinBox()
        self.planet_phase_box.setDecimals(3)
        self.planet_phase_box.setRange(0.0, 360.0)
        self.planet_phase_box.setSingleStep(1.0)
        self.planet_phase_box.valueChanged.connect(self._onParamsChanged)

        # earth eccentricity input
        self.earth_e_label = QLabel("eccentricity (Earth)")
        self.earth_e_box = QDoubleSpinBox()
        self.earth_e_box.setDecimals(3)
        self.earth_e_box.setRange(0.0, 1.0)
        self.earth_e_box.setSingleStep(0.01)
        self.earth_e_box.valueChanged.connect(self._onParamsChanged)

        # earth phase input
        self.earth_phase_label = QLabel("phase (planet) [deg]")
        self.earth_phase_box = QDoubleSpinBox()
        self.earth_phase_box.setDecimals(3)
        self.earth_phase_box.setRange(0.0, 360.0)
        self.earth_phase_box.setSingleStep(1.0)
        self.earth_phase_box.valueChanged.connect(self._onParamsChanged)
        
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
            model_earth_x = self.planetCoordinates.model_earth_x
            model_earth_y = self.planetCoordinates.model_earth_y
            self.ax.plot(model_earth_x, model_earth_y, 'b-', label="Earth's Orbit")

            # Plot Target planet's orbit
            model_planet_x = self.planetCoordinates.model_planet_x
            model_planet_y = self.planetCoordinates.model_planet_y
            self.ax.plot(model_planet_x, model_planet_y, 'r-', label=f"{self.planetCoordinates.selected_planet}'s Orbit")
            print()

            # Add legend
            self.ax.legend()
        
        self.plotCanvas.draw()

    def _onParamsChanged(self):
        """Update model parameters and refresh plot when any parameter changes."""
        self.planetCoordinates.planet_a = self.planet_a_box.value()
        self.planetCoordinates.planet_e = self.planet_e_box.value()
        self.planetCoordinates.planet_phase = np.deg2rad(self.planet_phase_box.value())
        self.planetCoordinates.earth_e = self.earth_e_box.value()
        self.planetCoordinates.earth_phase = np.deg2rad(self.earth_phase_box.value())
        # Recompute positions for the current planet and date
        if self.planetCoordinates.selected_planet is not None:
            self.planetCoordinates.set_planet_positions(self.planetCoordinates.dates[0])
            self.planetCoordinates.set_model_positions()
            self._loadData()

    def _onPlanetSelected(self, selected_planet):
        """Handle planet selection from the dropdown menu."""
        #self.planetCoordinates.set_selected_planet(selected_planet)
        #self._loadData()  # Reload the data and update the plot
        for widget in [self.planet_a_label, self.planet_a_box,
                    self.planet_e_label, self.planet_e_box,
                    self.planet_phase_label, self.planet_phase_box,
                    self.earth_e_label, self.earth_e_box,
                    self.earth_phase_label, self.earth_phase_box,]:
            self.optionsLayout.removeWidget(widget)
            widget.setParent(None)

        if selected_planet == "Select a planet":
            self.planetCoordinates.set_selected_planet(None)
            self._loadData()
            return

        # Block signals while setting default values
        self.planet_a_box.blockSignals(True)
        self.planet_e_box.blockSignals(True)
        self.planet_phase_box.blockSignals(True)
        self.earth_e_box.blockSignals(True)
        self.earth_phase_box.blockSignals(True)

        # Set default values
        self.planetCoordinates.set_selected_planet(selected_planet)
        self.planet_a_box.setValue(self.planetCoordinates.planet_a)
        self.planet_e_box.setValue(self.planetCoordinates.planet_e)
        self.planet_phase_box.setValue(self.planetCoordinates.planet_phase)
        self.earth_e_box.setValue(self.planetCoordinates.earth_e)
        self.earth_phase_box.setValue(self.planetCoordinates.earth_phase)

        # Unblock signals
        self.planet_a_box.blockSignals(False)
        self.planet_e_box.blockSignals(False)
        self.planet_phase_box.blockSignals(False)
        self.earth_e_box.blockSignals(False)
        self.earth_phase_box.blockSignals(False)

        # Now trigger the update only once
        self._onParamsChanged()

        # Update labels
        self.planet_a_label = QLabel(
            f"semi-major axis ({self.planetCoordinates.selected_planet}) [AU]")
        self.planet_e_label = QLabel(
            f"eccentricity ({self.planetCoordinates.selected_planet})")
        self.planet_phase_label = QLabel(
            f"phase ({self.planetCoordinates.selected_planet}) [deg]")
        
        # Add parameter widgets
        self.optionsLayout.insertWidget(1, self.planet_a_label)
        self.optionsLayout.insertWidget(2, self.planet_a_box)
        self.optionsLayout.insertWidget(3, self.planet_e_label)
        self.optionsLayout.insertWidget(4, self.planet_e_box)
        self.optionsLayout.insertWidget(5, self.planet_phase_label)
        self.optionsLayout.insertWidget(6, self.planet_phase_box)
        self.optionsLayout.insertWidget(7, self.earth_e_label)
        self.optionsLayout.insertWidget(8, self.earth_e_box)
        self.optionsLayout.insertWidget(9, self.earth_phase_label)
        self.optionsLayout.insertWidget(10, self.earth_phase_box)
        
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