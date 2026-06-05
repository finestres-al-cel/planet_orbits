"""Defines the CoordinatesView class."""
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QLabel, QDoubleSpinBox, QPushButton
)

from planet_orbits.app.error_dialog import ErrorDialog
from planet_orbits.app.success_dialog import SuccessDialog

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
    def __init__(self, planetOrbitalSolver, parent=None):
        """Initialize the CoordinatesView.

        Arguments
        ---------
        planetOrbitalSolver: PlanetOrbitalSolver
        An instance of the PlanetOrbitalSolver class that provides planet coordinates data.

        parent: QWidget - default: None
        The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Planet Coordinates")

        self.planetOrbitalSolver = planetOrbitalSolver
        self.planetSelector = None
        
        self.ax = None

        # Main layout
        self.mainLayout = QHBoxLayout(self)

        # Plot area
        self.plotCanvas = FigureCanvas(Figure(figsize=(8, 8)))
        self._setupPlot()
        self.mainLayout.addWidget(self.plotCanvas, stretch=3)

        # Options area
        """Old code
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
        """
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
            [planet.capitalize() for planet in self.planetOrbitalSolver.available_planets])  
        self.planetSelector.currentTextChanged.connect(self._onPlanetSelected)
        self.optionsLayout.addWidget(self.planetSelector)

        #################################################
        # Prepare parameter widgets but do not add yet, #
        # they will be added when a planet is selected  #
        #################################################

        # planet orbital period input
        self.planet_period_label = QLabel("Orbital period (planet) [days]")
        self.planet_period_box = QDoubleSpinBox()
        self.planet_period_box.setDecimals(5)
        self.planet_period_box.setRange(0.1, 10000.0)
        self.planet_period_box.setSingleStep(0.01)
        self.planet_period_box.valueChanged.connect(self._onParamsChanged)

        # earth orbital period input
        self.earth_period_label = QLabel("Orbital period (Earth) [days]")
        self.earth_period_box = QDoubleSpinBox()
        self.earth_period_box.setDecimals(5)
        self.earth_period_box.setRange(0.1, 10000.0)
        self.earth_period_box.setSingleStep(0.01)
        self.earth_period_box.valueChanged.connect(self._onParamsChanged)
        
        # Button to find oppositions
        self.findOppositionsButton = QPushButton("Find yearly series based on oppositions")
        self.findOppositionsButton.clicked.connect(self._onFindOppositions)
        
        """Old code
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
        self.earth_phase_label = QLabel("phase (Earth) [deg]")
        self.earth_phase_box = QDoubleSpinBox()
        self.earth_phase_box.setDecimals(3)
        self.earth_phase_box.setRange(0.0, 360.0)
        self.earth_phase_box.setSingleStep(1.0)
        self.earth_phase_box.valueChanged.connect(self._onParamsChanged)
        """

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

        # Load data from the planetOrbitalSolver object
        if self.planetOrbitalSolver.selected_planet is not None:
            
            # Plot Sun
            sun_x = self.planetOrbitalSolver.sun_x
            sun_y = self.planetOrbitalSolver.sun_y
            self.ax.plot(sun_x, sun_y, 'yo', label="Sun")

            # Plot Earth
            earth_x = np.concatenate(list(self.planetOrbitalSolver.earth_x.values()))
            earth_y = np.concatenate(list(self.planetOrbitalSolver.earth_y.values()))
            self.ax.plot(earth_x, earth_y, 'bo', label="Earth")

            # Plot selected planet
            planet_x = np.concatenate(list(self.planetOrbitalSolver.planet_x.values()))
            planet_y = np.concatenate(list(self.planetOrbitalSolver.planet_y.values()))
            self.ax.plot(planet_x, planet_y, 'ro', label=self.planetOrbitalSolver.selected_planet)

            # Plot Earth's orbit
            model_earth_x = self.planetOrbitalSolver.model_earth_x
            model_earth_y = self.planetOrbitalSolver.model_earth_y
            self.ax.plot(model_earth_x, model_earth_y, 'b-', label="Earth's Orbit")

            # Plot selected planet's orbit
            model_planet_x = self.planetOrbitalSolver.model_planet_x
            model_planet_y = self.planetOrbitalSolver.model_planet_y
            self.ax.plot(model_planet_x, model_planet_y, 'r-', label=f"{self.planetOrbitalSolver.selected_planet}'s Orbit")
            print()

            # Add legend
            self.ax.legend()
        
        self.plotCanvas.draw()

    def _onFindOppositions(self):
        """Handle the Find Oppositions button click.
        
        This method will find the dates of oppositions for the selected planet and display them in a dialog.
        """
        if self.planetOrbitalSolver.selected_planet is None:
            errorDialog = ErrorDialog("Please select a planet first.")
            errorDialog.exec()
            return
        
        oppositions = self.planetOrbitalSolver.find_oppositions()
        if oppositions.size == 0:
            infoDialog = ErrorDialog(f"No oppositions found for the planet {self.planetOrbitalSolver.selected_planet.capitalize()}.")
            infoDialog.exec()
        else:
            series_lengths = self.planetOrbitalSolver.find_oppositions_series()
            message = f"Found {oppositions.size} oppositions for the planet {self.planetOrbitalSolver.selected_planet.capitalize()}:\n\n"
            for opposition, series_length in zip(oppositions, series_lengths):
                message += opposition.strftime('%Y-%m-%d %H:%M:%S') + f" (Series length: {series_length})\n"
            oppositionsDialog = SuccessDialog(message)
            oppositionsDialog.exec()
        

    def _onParamsChanged(self):
        """Update model parameters and refresh plot when any parameter changes."""
        
        """Old code
        self.planetOrbitalSolver.planet_a = self.planet_a_box.value()
        self.planetOrbitalSolver.planet_e = self.planet_e_box.value()
        self.planetOrbitalSolver.planet_phase = np.deg2rad(self.planet_phase_box.value())
        self.planetOrbitalSolver.earth_e = self.earth_e_box.value()
        self.planetOrbitalSolver.earth_phase = np.deg2rad(self.earth_phase_box.value())
        # Recompute positions for the current planet and date
        if self.planetOrbitalSolver.selected_planet is not None:
            self.planetOrbitalSolver.set_planet_positions(self.planetOrbitalSolver.dates[0])
            self.planetOrbitalSolver.set_model_positions()
            self._loadData()
        """

    def _onPlanetSelected(self, selected_planet):
        """Handle planet selection from the dropdown menu."""
        for widget in [self.planet_period_label, self.planet_period_box,
                       self.earth_period_label, self.earth_period_box,
                       ]:
            self.optionsLayout.removeWidget(widget)
            widget.setParent(None)

        if selected_planet == "Select a planet":
            self.planetOrbitalSolver.set_selected_planet(None)
            self._loadData()
            return
        
        # Block signals while setting default values# Block signals while setting default values
        self.planet_period_box.blockSignals(True)
        self.earth_period_box.blockSignals(True)    

        # Set default values
        self.planetOrbitalSolver.set_selected_planet(selected_planet.lower())
        self.planet_period_box.setValue(self.planetOrbitalSolver.planet_period)
        self.earth_period_box.setValue(self.planetOrbitalSolver.earth_period)  

        # Unblock signals
        self.planet_period_box.blockSignals(False)
        self.earth_period_box.blockSignals(False)

        # Now trigger the update only once
        self._onParamsChanged()

        # Update labels
        self.planet_period_label = QLabel(
            f"Orbital period ({self.planetOrbitalSolver.selected_planet.capitalize()}) [days]")
        
        # Add parameter widgets
        self.optionsLayout.insertWidget(1, self.planet_period_label)
        self.optionsLayout.insertWidget(2, self.planet_period_box)
        self.optionsLayout.insertWidget(3, self.earth_period_label)
        self.optionsLayout.insertWidget(4, self.earth_period_box)
        self.optionsLayout.insertWidget(5, self.findOppositionsButton)

        """Old code
        #self.planetOrbitalSolver.set_selected_planet(selected_planet)
        #self._loadData()  # Reload the data and update the plot
        for widget in [self.planet_a_label, self.planet_a_box,
                    self.planet_e_label, self.planet_e_box,
                    self.planet_phase_label, self.planet_phase_box,
                    self.earth_e_label, self.earth_e_box,
                    self.earth_phase_label, self.earth_phase_box,]:
            self.optionsLayout.removeWidget(widget)
            widget.setParent(None)

        if selected_planet == "Select a planet":
            self.planetOrbitalSolver.set_selected_planet(None)
            self._loadData()
            return

        # Block signals while setting default values
        self.planet_a_box.blockSignals(True)
        self.planet_e_box.blockSignals(True)
        self.planet_phase_box.blockSignals(True)
        self.earth_e_box.blockSignals(True)
        self.earth_phase_box.blockSignals(True)

        # Set default values
        self.planetOrbitalSolver.set_selected_planet(selected_planet)
        self.planet_a_box.setValue(self.planetOrbitalSolver.planet_a)
        self.planet_e_box.setValue(self.planetOrbitalSolver.planet_e)
        self.planet_phase_box.setValue(self.planetOrbitalSolver.planet_phase)
        self.earth_e_box.setValue(self.planetOrbitalSolver.earth_e)
        self.earth_phase_box.setValue(self.planetOrbitalSolver.earth_phase)

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
            f"semi-major axis ({self.planetOrbitalSolver.selected_planet}) [AU]")
        self.planet_e_label = QLabel(
            f"eccentricity ({self.planetOrbitalSolver.selected_planet})")
        self.planet_phase_label = QLabel(
            f"phase ({self.planetOrbitalSolver.selected_planet}) [deg]")
        
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

        """      

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