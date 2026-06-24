"""Defines the CoordinatesView class."""
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QLabel, QDoubleSpinBox, QPushButton
)

from planet_orbits.app.error_dialog import ErrorDialog
from planet_orbits.app.oppositions_dialog import OppositionsDialog

FIND_OPPOSITIONS_BUTTON_TEXT = "Find yearly series based on oppositions"
FIND_OPPOSITIONS_BUTTON_TEXT_UPDATE = "Find yearly series based on oppositions (update)"
PLOT_DATA_BUTTON_TEXT = "Plot Data"
PLOT_DATA_BUTTON_TEXT_UPDATE = "Plot Data (update)"

ORBITAL_PARAM_DECIMALS = 5
ORBITAL_PARAM_CHANGE_TOLERANCE = 10 ** (-ORBITAL_PARAM_DECIMALS)


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
        
        self.ax = None

        # Main layout
        self.mainLayout = QHBoxLayout(self)

        # Metrics variables
        self.chi2_planet_label = None
        self.dispersion_label = None
        self.metric_series_table_title = None
        self.metric_series_table = None

        # Metrics area
        self.metricsLayout = QVBoxLayout()
        self._setupMetrics()
        self.mainLayout.addLayout(self.metricsLayout, stretch=1)
        
        # Plot area
        self.plotCanvas = FigureCanvas(Figure(figsize=(8, 8)))
        self._setupPlot()
        self.mainLayout.addWidget(self.plotCanvas, stretch=3)

        # Planet selection box 
        self.planetSelector = None
        
        # Period options box
        self.planet_period_label = None
        self.planet_period_box = None
        self.earth_period_label = None
        self.earth_period_box = None

        # find oppositions button
        self.findOppositionsButton = None

        # Orbital parameters options box
        self.planet_semimajor_axis_label = None
        self.planet_semimajor_axis_box = None
        self.planet_eccentricity_label = None
        self.planet_eccentricity_box = None
        self.planet_phase_label = None
        self.planet_phase_box = None
        self.earth_semimajor_axis_label = None
        self.earth_semimajor_axis_box = None
        self.earth_eccentricity_label = None
        self.earth_eccentricity_box = None
        self.earth_phase_label = None
        self.earth_phase_box = None
        self.optionsLayout = None

        # plot button
        self.plotButton = None

        # active widgets
        self.activePeriodWidgets = []
        self.activeOrbitalParamWidgets = []

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
        self.planet_period_box.setRange(0.001, 70000.0)
        self.planet_period_box.setSingleStep(0.01)
        self.planet_period_box.valueChanged.connect(self._onPeriodsChanged)

        # earth orbital period input
        self.earth_period_label = QLabel("Orbital period (Earth) [days]")
        self.earth_period_box = QDoubleSpinBox()
        self.earth_period_box.setDecimals(5)
        self.earth_period_box.setRange(0.001, 70000.0)
        self.earth_period_box.setSingleStep(0.01)
        self.earth_period_box.valueChanged.connect(self._onPeriodsChanged)
        
        # Button to find oppositions
        self.findOppositionsButton = QPushButton(FIND_OPPOSITIONS_BUTTON_TEXT)
        self.findOppositionsButton.clicked.connect(self._onFindOppositions)
        
        #################################################
        # Prepare parameter widgets but do not add yet, #
        # they will be added when the oppositions       #
        # series are computed                           #
        #################################################

        # planet semi-major axis input
        self.planet_semimajor_axis_label = QLabel("semi-major axis (planet) [AU]")
        self.planet_semimajor_axis_box = QDoubleSpinBox()
        self.planet_semimajor_axis_box.setDecimals(ORBITAL_PARAM_DECIMALS)
        self.planet_semimajor_axis_box.setRange(0.1, 100.0)
        self.planet_semimajor_axis_box.setSingleStep(ORBITAL_PARAM_CHANGE_TOLERANCE)
        self.planet_semimajor_axis_box.valueChanged.connect(self._onOrbitalParamsChanged)

        # planet eccentricity input
        self.planet_eccentricity_label = QLabel("eccentricity (planet)")
        self.planet_eccentricity_box = QDoubleSpinBox()
        self.planet_eccentricity_box.setDecimals(ORBITAL_PARAM_DECIMALS)
        self.planet_eccentricity_box.setRange(0.0, 1.0)
        self.planet_eccentricity_box.setSingleStep(ORBITAL_PARAM_CHANGE_TOLERANCE)
        self.planet_eccentricity_box.valueChanged.connect(self._onOrbitalParamsChanged)

        # planet phase input
        self.planet_phase_label = QLabel("phase (planet) [deg]")
        self.planet_phase_box = QDoubleSpinBox()
        self.planet_phase_box.setDecimals(ORBITAL_PARAM_DECIMALS)
        self.planet_phase_box.setRange(0.0, 360.0)
        self.planet_phase_box.setSingleStep(ORBITAL_PARAM_CHANGE_TOLERANCE)
        self.planet_phase_box.valueChanged.connect(self._onOrbitalParamsChanged)

        # planet semi-major axis input
        self.earth_semimajor_axis_label = QLabel("semi-major axis (Earth) [AU]")
        self.earth_semimajor_axis_box = QDoubleSpinBox()
        self.earth_semimajor_axis_box.setDecimals(ORBITAL_PARAM_DECIMALS)
        self.earth_semimajor_axis_box.setRange(0.1, 100.0)
        self.earth_semimajor_axis_box.setSingleStep(ORBITAL_PARAM_CHANGE_TOLERANCE)
        self.earth_semimajor_axis_box.valueChanged.connect(self._onOrbitalParamsChanged)

        # earth eccentricity input
        self.earth_eccentricity_label = QLabel("eccentricity (Earth)")
        self.earth_eccentricity_box = QDoubleSpinBox()
        self.earth_eccentricity_box.setDecimals(ORBITAL_PARAM_DECIMALS)
        self.earth_eccentricity_box.setRange(0.0, 1.0)
        self.earth_eccentricity_box.setSingleStep(ORBITAL_PARAM_CHANGE_TOLERANCE)
        self.earth_eccentricity_box.valueChanged.connect(self._onOrbitalParamsChanged)

        # earth phase input
        self.earth_phase_label = QLabel("phase (Earth) [deg]")
        self.earth_phase_box = QDoubleSpinBox()
        self.earth_phase_box.setDecimals(ORBITAL_PARAM_DECIMALS)
        self.earth_phase_box.setRange(0.0, 360.0)
        self.earth_phase_box.setSingleStep(ORBITAL_PARAM_CHANGE_TOLERANCE)
        self.earth_phase_box.valueChanged.connect(self._onOrbitalParamsChanged)

        # Button to plot data
        self.plotDataButton = QPushButton(PLOT_DATA_BUTTON_TEXT)
        self.plotDataButton.clicked.connect(self._onPlotData)

        ###########################
        # Push buttons to the top # 
        ###########################  
        self.optionsLayout.addStretch(1) 
        optionsBox.setLayout(self.optionsLayout)

        return optionsBox

    def _onFindOppositions(self):
        """Handle the Find Oppositions button click.
        
        This method will find the dates of oppositions for the selected planet and display them in a dialog.
        """
        if self.planetOrbitalSolver.selected_planet is None:
            errorDialog = ErrorDialog("Please select a planet first.")
            errorDialog.exec()
            return
        
        # if 'update' is in the button text, it means that the periods have been changed but the oppositions 
        # series have not been updated, so we need to update them before showing the dialog
        if "update" in self.findOppositionsButton.text():
            self.planetOrbitalSolver.planet_period = self.planet_period_box.value()
            self.planetOrbitalSolver.earth_period = self.earth_period_box.value()
            self.planetOrbitalSolver.reset_opposition_data()
            # now remove the 'update' text from the button to indicate that the oppositions series are now updated
            self.findOppositionsButton.setText(FIND_OPPOSITIONS_BUTTON_TEXT)

        # if 'update' is in the the plot data button, it means that the orbital parameters have been changed but the 
        # plot data has not been updated, so we need to update the orbital parameters in the model before showing the dialog
        # otherwise changes would be lost
        if self.plotDataButton in self.activeOrbitalParamWidgets and "update" in self.plotDataButton.text():
            self.planetOrbitalSolver.planet_semimajor_axis = self.planet_semimajor_axis_box.value()
            self.planetOrbitalSolver.planet_eccentricity = self.planet_eccentricity_box.value()
            self.planetOrbitalSolver.planet_phase = np.deg2rad(self.planet_phase_box.value())
            self.planetOrbitalSolver.earth_semimajor_axis = self.earth_semimajor_axis_box.value()
            self.planetOrbitalSolver.earth_eccentricity = self.earth_eccentricity_box.value()
            self.planetOrbitalSolver.earth_phase = np.deg2rad(self.earth_phase_box.value())
            self.plotDataButton.setText(PLOT_DATA_BUTTON_TEXT)
            
        # now find the oppositions and show the dialog
        oppositions = self.planetOrbitalSolver.find_oppositions()
        if oppositions.size == 0:
            infoDialog = ErrorDialog(f"No oppositions found for the planet {self.planetOrbitalSolver.selected_planet.capitalize()}.")
            infoDialog.exec()
        else:            
            series_lengths, plot_flags = self.planetOrbitalSolver.find_oppositions_series()
            oppositionsDialog = OppositionsDialog(
                self.planetOrbitalSolver.selected_planet,
                oppositions,
                series_lengths,
                plot_flags,
                parent=self,
            )
            if oppositionsDialog.exec():
                selected_rows = oppositionsDialog.selected_rows_to_plot()
    
                self.planetOrbitalSolver.data_oppositions_series_plot = selected_rows

        ############################################
        # Add widgets to select orbital parameters #
        ############################################

        # reset current widget list
        self.planetOrbitalSolver.reset_orbital_parameters()
        for widget in self.activeOrbitalParamWidgets:
            self.optionsLayout.removeWidget(widget)
            widget.setParent(None)
        self.activeOrbitalParamWidgets = []

        # Block signals while setting default values
        self.planet_semimajor_axis_box.blockSignals(True)
        self.planet_eccentricity_box.blockSignals(True)
        self.planet_phase_box.blockSignals(True)
        self.earth_semimajor_axis_box.blockSignals(True)
        self.earth_eccentricity_box.blockSignals(True)
        self.earth_phase_box.blockSignals(True)

        # Set default values
        self.planet_semimajor_axis_box.setValue(self.planetOrbitalSolver.planet_semimajor_axis)
        self.planet_eccentricity_box.setValue(self.planetOrbitalSolver.planet_eccentricity)
        self.planet_phase_box.setValue(self.planetOrbitalSolver.planet_phase)
        self.earth_semimajor_axis_box.setValue(self.planetOrbitalSolver.earth_semimajor_axis)
        self.earth_eccentricity_box.setValue(self.planetOrbitalSolver.earth_eccentricity)
        self.earth_phase_box.setValue(self.planetOrbitalSolver.earth_phase)

        # Unblock signals
        self.planet_semimajor_axis_box.blockSignals(False)
        self.planet_eccentricity_box.blockSignals(False)
        self.planet_phase_box.blockSignals(False)
        self.earth_semimajor_axis_box.blockSignals(False)
        self.earth_eccentricity_box.blockSignals(False)
        self.earth_phase_box.blockSignals(False)

        # Update labels
        self.planet_semimajor_axis_label = QLabel(
            f"semi-major axis ({self.planetOrbitalSolver.selected_planet.capitalize()}) [AU]")
        self.planet_eccentricity_label = QLabel(
            f"eccentricity ({self.planetOrbitalSolver.selected_planet.capitalize()})")
        self.planet_phase_label = QLabel(
            f"phase ({self.planetOrbitalSolver.selected_planet.capitalize()}) [deg]")
        
        # Add parameter widgets
        self.optionsLayout.insertWidget(6, self.planet_semimajor_axis_label)
        self.optionsLayout.insertWidget(7, self.planet_semimajor_axis_box)
        self.optionsLayout.insertWidget(8, self.planet_eccentricity_label)
        self.optionsLayout.insertWidget(9, self.planet_eccentricity_box)
        self.optionsLayout.insertWidget(10, self.planet_phase_label)
        self.optionsLayout.insertWidget(11, self.planet_phase_box)
        self.optionsLayout.insertWidget(12, self.earth_semimajor_axis_label)
        self.optionsLayout.insertWidget(13, self.earth_semimajor_axis_box)
        self.optionsLayout.insertWidget(14, self.earth_eccentricity_label)
        self.optionsLayout.insertWidget(15, self.earth_eccentricity_box)
        self.optionsLayout.insertWidget(16, self.earth_phase_label)
        self.optionsLayout.insertWidget(17, self.earth_phase_box)
        self.optionsLayout.insertWidget(18, self.plotDataButton)

        # Keep track of active widgets to remove them later when a new planet is selected
        self.activeOrbitalParamWidgets += [
            self.planet_semimajor_axis_label,
            self.planet_semimajor_axis_box,
            self.planet_eccentricity_label,
            self.planet_eccentricity_box,
            self.planet_phase_label,
            self.planet_phase_box,
            self.earth_semimajor_axis_label,
            self.earth_semimajor_axis_box,
            self.earth_eccentricity_label,
            self.earth_eccentricity_box,
            self.earth_phase_label,
            self.earth_phase_box,
            self.plotDataButton
        ]

        # plot data with the new parameters
        self._onPlotData()

    def _onOrbitalParamsChanged(self, _value=None, force_update=False):
        """Update model parameters and refresh plot when any parameter changes.
        
        Arguments
        ---------
        _value : float, optional
        Value forwarded by Qt's valueChanged signal.

        force_update : bool, optional
        If True, forces the changes the label to indicate the need for an update, 
        even if there are no actual changes in the parameters.
        """
        if self.plotDataButton not in self.activeOrbitalParamWidgets:
            self.plotDataButton.setText(PLOT_DATA_BUTTON_TEXT)
            return

        new_planet_semimajor_axis = self.planet_semimajor_axis_box.value()
        new_planet_eccentricity = self.planet_eccentricity_box.value()
        new_planet_phase = self.planet_phase_box.value()
        new_earth_semimajor_axis = self.earth_semimajor_axis_box.value()
        new_earth_eccentricity = self.earth_eccentricity_box.value()
        new_earth_phase = self.earth_phase_box.value()

        # check if there are changes in the orbital parameters
        changes = [
            not np.isclose(
                new_planet_semimajor_axis,
                self.planetOrbitalSolver.planet_semimajor_axis,
                atol=ORBITAL_PARAM_CHANGE_TOLERANCE,
                rtol=0.0,
            ),
            not np.isclose(
                new_planet_eccentricity,
                self.planetOrbitalSolver.planet_eccentricity,
                atol=ORBITAL_PARAM_CHANGE_TOLERANCE,
                rtol=0.0,
            ),
            not np.isclose(
                new_planet_phase,
                np.rad2deg(self.planetOrbitalSolver.planet_phase),
                atol=ORBITAL_PARAM_CHANGE_TOLERANCE,
                rtol=0.0,
            ),
            not np.isclose(
                new_earth_semimajor_axis,
                self.planetOrbitalSolver.earth_semimajor_axis,
                atol=ORBITAL_PARAM_CHANGE_TOLERANCE,
                rtol=0.0,
            ),
            not np.isclose(
                new_earth_eccentricity,
                self.planetOrbitalSolver.earth_eccentricity,
                atol=ORBITAL_PARAM_CHANGE_TOLERANCE,
                rtol=0.0,
            ),
            not np.isclose(
                new_earth_phase,
                np.rad2deg(self.planetOrbitalSolver.earth_phase),
                atol=ORBITAL_PARAM_CHANGE_TOLERANCE,
                rtol=0.0,
            )
        ]

        # if here are, change the label of the data plot button to indicate the need for an update
        # the actual values will be updated when the user clicks the data plot button, 
        # to avoid unnecessary updates when the user is just adjusting the periods
        if any(changes) or force_update:
            self.plotDataButton.setText(PLOT_DATA_BUTTON_TEXT_UPDATE)
        else:
            self.plotDataButton.setText(PLOT_DATA_BUTTON_TEXT)

    def _onPeriodsChanged(self):
        """Update model periods and refresh plot when any period changes."""
    
        new_planet_period = self.planet_period_box.value()
        new_earth_period = self.earth_period_box.value()

        # check if there are changes in the periods
        # if here are, change the label of the find oppositions button to indicate the need for an update
        # the actual values will be updated when the user clicks the find oppositions button, 
        # to avoid unnecessary updates when the user is just adjusting the periods
        if new_planet_period != self.planetOrbitalSolver.planet_period or new_earth_period != self.planetOrbitalSolver.earth_period:            
            self.findOppositionsButton.setText(FIND_OPPOSITIONS_BUTTON_TEXT_UPDATE)
            # also indicate that the plot data needs to be updated since the periods affect the plot
            if self.plotDataButton in self.activeOrbitalParamWidgets:
                self._onOrbitalParamsChanged(force_update=True)
        else:
            self.findOppositionsButton.setText(FIND_OPPOSITIONS_BUTTON_TEXT)
            # reset the plot data button text in case it was changed due to previous changes in the periods
            if self.plotDataButton in self.activeOrbitalParamWidgets:
                self._onOrbitalParamsChanged()


    def _onPlanetSelected(self, selected_planet):
        """Handle planet selection from the dropdown menu."""
        # if planet is unchanged, do nothing
        if selected_planet == self.planetOrbitalSolver.selected_planet:
            return

        # remove widgets related to the previously selected planet, if any
        for widget in self.activePeriodWidgets + self.activeOrbitalParamWidgets:
            self.optionsLayout.removeWidget(widget)
            widget.setParent(None)
        self.activePeriodWidgets = []
        self.activeOrbitalParamWidgets = []
        if selected_planet == "Select a planet":
            self.planetOrbitalSolver.set_selected_planet(None)
            return

        #############################################
        # Add widgets to compute oppositions series #
        #############################################
        # Block signals while setting default values
        self.planet_period_box.blockSignals(True)
        self.earth_period_box.blockSignals(True)

        # Set default values
        self.planetOrbitalSolver.set_selected_planet(selected_planet.lower())
        self.planet_period_box.setValue(self.planetOrbitalSolver.planet_period)
        self.planet_period = self.planetOrbitalSolver.planet_period
        self.earth_period_box.setValue(self.planetOrbitalSolver.earth_period)
        self.earth_period = self.planetOrbitalSolver.earth_period

        # Unblock signals
        self.planet_period_box.blockSignals(False)
        self.earth_period_box.blockSignals(False)

        # Now trigger the update only once
        self._onPeriodsChanged()

        # Update labels
        self.planet_period_label = QLabel(
            f"Orbital period ({self.planetOrbitalSolver.selected_planet.capitalize()}) [days]")

        # Add parameter widgets
        self.optionsLayout.insertWidget(1, self.planet_period_label)
        self.optionsLayout.insertWidget(2, self.planet_period_box)
        self.optionsLayout.insertWidget(3, self.earth_period_label)
        self.optionsLayout.insertWidget(4, self.earth_period_box)
        self.optionsLayout.insertWidget(5, self.findOppositionsButton)

        # Keep track of active widgets to remove them later when a new planet is selected
        self.activePeriodWidgets += [
            self.planet_period_label,
            self.planet_period_box,
            self.earth_period_label,
            self.earth_period_box,
            self.findOppositionsButton
        ]

        # update the metrics area with the new planet name
        self._resetMetrics()

    def _onPlotData(self):
        """Handle the Plot Data button click."""
        # update the model parameters with the current values in the boxes before plotting
        self.planetOrbitalSolver.planet_semimajor_axis = self.planet_semimajor_axis_box.value()
        self.planetOrbitalSolver.planet_eccentricity = self.planet_eccentricity_box.value()
        self.planetOrbitalSolver.planet_phase = np.deg2rad(self.planet_phase_box.value())
        self.planetOrbitalSolver.earth_semimajor_axis = self.earth_semimajor_axis_box.value()
        self.planetOrbitalSolver.earth_eccentricity = self.earth_eccentricity_box.value()
        self.planetOrbitalSolver.earth_phase = np.deg2rad(self.earth_phase_box.value())

        # find the planet coordinates with the new parameters
        self.planetOrbitalSolver.find_planet_coordinates()

        # compute orbital models
        self.planetOrbitalSolver.compute_orbital_models()

        # plot them
        self._plotData()

        # update the plot data button text to indicate that the plot is now updated
        self.plotDataButton.setText(PLOT_DATA_BUTTON_TEXT)

    def _plotData(self):
        """Load data and update the plot."""
        # clear previous plot
        if self.ax is not None:
            self._resetPlot()
        else:
            self._setupPlot()

        # Load data from the planetOrbitalSolver object
        if self.planetOrbitalSolver.selected_planet is not None:
            
            # Plot Sun
            sun_x, sun_y = self.planetOrbitalSolver.sun_coordinates
            self.ax.plot(sun_x, sun_y, 'yo', label="Sun")

            for index, (date, (earth_x, earth_y)) in enumerate(self.planetOrbitalSolver.earth_coordinates.items()):
                if index == 0:
                    self.ax.plot(earth_x, earth_y, 'b.', label="Earth")
                else:
                    self.ax.plot(earth_x, earth_y, 'b.')

            # Plot selected planet
            for index, (date, (planet_x, planet_y)) in enumerate(self.planetOrbitalSolver.planet_coordinates.items()):
                if index == 0:
                    self.ax.plot(planet_x, planet_y, 'r.', label=self.planetOrbitalSolver.selected_planet)
                else:
                    self.ax.plot(planet_x, planet_y, 'r.')

            # Plot Earth's orbit
            model_earth_x, model_earth_y = self.planetOrbitalSolver.model_earth
            self.ax.plot(model_earth_x, model_earth_y, 'b-', label="Earth's Orbit")

            # Plot selected planet's orbit
            model_planet_x, model_planet_y = self.planetOrbitalSolver.model_planet
            self.ax.plot(model_planet_x, model_planet_y, 'r-', label=f"{self.planetOrbitalSolver.selected_planet}'s Orbit")


            # Add legend
            self.ax.legend()
        
        self.plotCanvas.draw()

        # update metrics to match the current plot
        self._updateMetrics()

    def _resetMetrics(self):
        """Reset the metrics displayed in the metrics area."""
        if self.planetOrbitalSolver.selected_planet is None:
            self.chi2_planet_label.setText("Planet orbit χ<sup>2</sup>: N/A")
        else:
            self.chi2_planet_label.setText(f"{self.planetOrbitalSolver.selected_planet.capitalize()} orbit χ<sup>2</sup>: N/A")
        self.dispersion_label.setText("Global radial dispersion (σ<sub>R</sub>) [AU]: N/A")
        self.metric_series_table.clearContents()
        self.metric_series_table.setRowCount(0)
        
    def _resetPlot(self):
        """Reset the plot to its initial state."""
        self.ax.clear()
        self.ax.set_title("Planet Positions")
        self.ax.set_xlabel("X [AU]")
        self.ax.set_ylabel("Y [AU]")
        self.ax.grid(True)
        self.ax.axis("equal")

    def _setupMetrics(self):
        """Set up the metrics area."""
        # Then show the chi2 for the planet and the earth separately
        self.chi2_planet_label = QLabel("Planet orbit χ<sup>2</sup>: N/A")
        
        # Show the overall dispersion in the computed values of r for the planet (sigma_R_planet)
        self.dispersion_label = QLabel("Global radial dispersion (σ<sub>R</sub>) [AU]: N/A")

        # Finally show a table with the dispersion in each of the oppositions series, if any
        # the table will have two columns: the first one with the opposition date and the second one with the dispersion in the computed values of r for that opposition series
        # only selected series will be shown in the table
        self.metric_series_table_title = QLabel("Selected series metrics:")
        self.metric_series_table = QTableWidget(0, 3)
        self.metric_series_table.setHorizontalHeaderLabels(["Opposition Date", "σ_R [AU]", "χ² (N_points)"])
        self.metric_series_table.verticalHeader().setVisible(False)
        self.metric_series_table.horizontalHeader().setStretchLastSection(True)
        
        self.metricsLayout.addWidget(self.chi2_planet_label)
        self.metricsLayout.addWidget(self.dispersion_label)
        self.metricsLayout.addWidget(self.metric_series_table_title)
        self.metricsLayout.addWidget(self.metric_series_table)

    def _setupPlot(self):
        """Set up the plot area."""
        self.ax = self.plotCanvas.figure.add_subplot(111)
        self.ax.set_title("Planet Positions")
        self.ax.set_xlabel("X [AU]")
        self.ax.set_ylabel("Y [AU]")
        self.ax.grid(True)
        self.ax.axis("equal")

    def _updateMetrics(self):
        """Update the metrics displayed in the metrics area."""
        # clear previous metrics
        self._resetMetrics()

        chi2_planet = self.planetOrbitalSolver.total_chi2
        num_points = self.planetOrbitalSolver.total_points
        total_dispersion = self.planetOrbitalSolver.total_dispersion

        self.chi2_planet_label.setText(f"Chi2 ({self.planetOrbitalSolver.selected_planet}): {chi2_planet:.5f}")
        self.dispersion_label.setText(
            f"Global radial dispersion (σ<sub>R</sub>) [AU]: {total_dispersion:.7f}"
        )

        # Update the oppositions dispersion table
        metrics = sorted(self.planetOrbitalSolver.metrics.items(), key=lambda item: item[0])
        self.metric_series_table.setRowCount(len(metrics))

        for row, (opposition_date, (dispersion, chi2, num_points)) in enumerate(metrics):
            date_item = QTableWidgetItem(opposition_date.strftime("%Y-%m-%d"))
            dispersion_item = QTableWidgetItem(f"{dispersion:.7f}")
            chi2_item = QTableWidgetItem(f"{chi2:.5f} ({num_points})")
            self.metric_series_table.setItem(row, 0, date_item)
            self.metric_series_table.setItem(row, 1, dispersion_item)
            self.metric_series_table.setItem(row, 2, chi2_item)