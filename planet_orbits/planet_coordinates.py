"""Define the PlanetCoordinates class to handle planet coordinates in a 
solar system simulation."""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from planet_orbits.errors import PlanetCoordinatesError
from planet_orbits.utils import find_theta_earth, get_date_indexs

# Number of model points to compute
N_MODEL_POINTS = 1000

# periods of planets in days
PLANET_PERIODS = {
    "Mercury": 88,
    "Venus": 225,
    "Earth": 365,
    "Mars": 687,
    "Jupiter": 4333,
    "Saturn": 10759,
    "Uranus": 30687,
    "Neptune": 60190,
}

class PlanetCoordinates:
    """
    Class to handle the coordinates of planets in a solar system simulation.
    """
    def __init__(self, filename):
        """
        Initialize the PlanetCoordinates class.

        Arguments
        ---------
        filename: str
        Path to the CSV file containing planet data.
        """
        self.filename = filename
        self.data = pd.read_csv(filename)
        self.start_date = self.data.loc[0, "Date"]
        self.end_date = self.data.loc[self.data.shape[0] - 1, "Date"]

        self.dates = []
        self.selected_planet = None
        self.planet_a = None # semi-major axis of the selected planet in AU
        self.planet_e = 0 # eccentricity of the selected planet
        
        self.earth_a = 1.0
        self.earth_e = 0
        self.earth_phase = 0.0
        self.relative_phase = 0.0 # relative phase of the selected planet with respect to Earth

        # When plotting the model, we assume that the planet's periastron is at the
        # x axis (-a_planet, 0) and the sun is at the centre (0, 0)
        # phase of the first date in the selected planet in radians (with respect to the periastsron)
        self.planet_phase = 0.0 
        # relative phase of the planet's periastron with respect to the Earth's
        self.relative_phase = 0.0  # relative phase of the selected planet with respect to Earth
        
        # Initialize lists to store positions
        # Positions are stored as np.arrays for date group
        # Date groups are defined by dates at which the target planet is in the 
        # same position, determined by the period of the planet
        # keys are the first date of the group
        self.earth_theta = {}
        self.earth_x = {}
        self.earth_y = {}
        self.planet_theta = {}
        self.planet_x = {}
        self.planet_y = {}
        self.sun_x = 0
        self.sun_y = 0

        # Initialize model positions
        self.model_time = None
        self.model_planet_x = None
        self.model_planet_y = None
        self.model_earth_x = None
        self.model_earth_y = None

    def reset_planet(self, planet_name):
        """
        Reset the selected planet and its properties.

        Arguments
        ---------
        planet_name: str
        Name of the planet to be reset.
        """
        self.dates = [self.start_date]

        self.earth_theta.clear()
        self.earth_x.clear()
        self.earth_y.clear()
        self.planet_theta.clear()
        self.planet_x.clear()
        self.planet_y.clear()

        if planet_name in ["Mercury", "Venus"]:
            self.planet_a = 0.5
        else:
            self.planet_a = 1.5
            # TODO: delte this line when the model is ready
            self.planet_a = 1.524  # Mars semi-major axis in AU
        self.planet_e = 0
        self.relative_phase = 0.0
        # TODO: delte this line when the model is ready
        self.planet_e = 0.0934  # Mars eccentricity
        self.earth_e = 0.0167  # Earth eccentricity

    def set_selected_planet(self, planet_name):
        """
        Set the selected planet for the simulation.

        Arguments
        ---------
        planet_name: str
        Name of the planet to be selected.
        """
        if planet_name is not None and planet_name not in PLANET_PERIODS:
            raise PlanetCoordinatesError(f"Invalid planet name: {planet_name}.")

        # Reset the active dates if changing the planet
        if self.selected_planet is None or self.selected_planet != planet_name:
            self.reset_planet(planet_name)

        self.selected_planet = planet_name
        if self.selected_planet is not None:
           self.set_planet_positions(self.dates[0])
           self.set_model_positions()

    def set_model_positions(self):
        """
        Compute the theoretical positions of the planets given the 
        selected planetary orbit parameters.
        Store them in the respective dictionaries.

        Raises
        ------
        PlanetCoordinatesError
            If no planet is selected.
        """
        if self.selected_planet is None:
            raise PlanetCoordinatesError("No planet selected.")

        # Get the period of the selected planet
        planet_period = PLANET_PERIODS[self.selected_planet]
        earth_period = PLANET_PERIODS["Earth"]

        self.model_time_planet = np.linspace(
            0, planet_period, N_MODEL_POINTS) # days 

        self.model_time_earth = np.linspace(
            0, earth_period, N_MODEL_POINTS)  # days

        #######################
        # target planet model #
        #######################
        planet_theta = np.pi - (2 * np.pi / planet_period) * self.model_time_planet
        planet_r = self.planet_a * (1 - self.planet_e**2) / (1 + self.planet_e * np.cos(planet_theta - self.planet_phase))
        self.model_planet_x = planet_r * np.cos(planet_theta)
        self.model_planet_y = planet_r * np.sin(planet_theta)

        ###############
        # Earth model #
        ###############
        earth_theta = np.pi - (2 * np.pi / earth_period) * self.model_time_earth
        earth_r = self.earth_a * (1 - self.earth_e**2) / (1 + self.earth_e * np.cos(earth_theta - self.earth_phase))
        self.model_earth_x = earth_r * np.cos(earth_theta)
        self.model_earth_y = earth_r * np.sin(earth_theta)

    def set_planet_positions(self, date):
        """
        Compute the positions of the planets for a given date.
        Store them in the respective dictionaries.

        Arguments
        ---------
        date: str
        Date for which to compute the positions.

        Raises
        ------
        PlanetCoordinatesError
            If no planet is selected or if the date is not in the data.
        """
        if self.selected_planet is None:
            raise PlanetCoordinatesError("No planet selected.")

        # Get the indexs of the selected dates
        planet_period = PLANET_PERIODS[self.selected_planet]
        indexs = get_date_indexs(date, self.end_date, planet_period, self.data["Date"])

        ##########################
        # target planet position #
        ##########################
    
        # Calculate the position of the selected planet
        planet_theta = self.data.loc[indexs, f"{self.selected_planet}_lon"].values[:1]
        planet_r = self.planet_a * (1 - self.planet_e**2) / (1 + self.planet_e * np.cos(planet_theta))
        planet_x = planet_r * np.cos(planet_theta)
        planet_y = planet_r * np.sin(planet_theta)
        
        # Keep planet position
        self.planet_theta[date] = planet_theta
        self.planet_x[date] = planet_x
        self.planet_y[date] = planet_y

        ###################
        # Earth positions #
        ###################

        # Assuming Earth and the selected planet are coplanar
        earth_theta = self.data.loc[indexs, f"Earth_lon"].values
        earth_r = self.earth_a * (1 - self.earth_e**2) / (1 + self.earth_e * np.cos(earth_theta))
        earth_x = earth_r * np.cos(earth_theta)
        earth_y = earth_r * np.sin(earth_theta)
        
        # Keep Earth position 
        self.earth_theta[date] = earth_theta # Earth angle with respect to Sun
        self.earth_x[date] = earth_x
        self.earth_y[date] = earth_y
        