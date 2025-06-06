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
        self.a_planet = None
        self.e_planet = 0
        self.a_earth = 1.0
        self.e_earth = 0

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
        self.model_x_planet = None
        self.model_y_planet = None
        self.model_x_earth = None
        self.model_y_earth = None

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
            self.a_planet = 0.5
        else:
            self.a_planet = 1.5
            # TODO: delte this line when the model is ready
            self.a_planet = 1.524  # Mars semi-major axis in AU
        self.e_planet = 0
        # TODO: delte this line when the model is ready
        self.e_planet = 0.0934  # Mars eccentricity
        self.e_earth = 0.0167  # Earth eccentricity


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

        # Set the model time based on the period of the selected planet
        # and the Earth
        if self.selected_planet in ["Mercury", "Venus"]:
            self.model_time = np.linspace(
                0, earth_period, N_MODEL_POINTS)  # days
        else:
            self.model_time = np.linspace(
                0, planet_period, N_MODEL_POINTS) # days 

        #######################
        # target planet model #
        #######################
        theta_planet = np.pi - (2 * np.pi / planet_period) * self.model_time
        r_planet = self.a_planet * (1 - self.e_planet**2) / (1 + self.e_planet * np.cos(theta_planet))
        self.model_x_planet = r_planet * np.cos(theta_planet)
        self.model_y_planet = r_planet * np.sin(theta_planet)

        ###############
        # Earth model #
        ###############
        theta_earth = np.pi - (2 * np.pi / earth_period) * self.model_time
        r_earth = self.a_earth * (1 - self.e_earth**2) / (1 + self.e_earth * np.cos(theta_earth))
        self.model_x_earth = r_earth * np.cos(theta_earth)
        self.model_y_earth = r_earth * np.sin(theta_earth)

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

        # Get the period of the selected planet
        planet_period = PLANET_PERIODS[self.selected_planet]
        earth_period = PLANET_PERIODS["Earth"]

        ##########################
        # target planet position #
        ##########################
    
        # Calculate the number of days since the start date
        start_date = datetime.strptime(self.dates[0], "%Y-%m-%d")
        current_date = datetime.strptime(date, "%Y-%m-%d")
        days_since_start = (current_date - start_date).days

        # Calculate the position of the selected planet
        theta_planet = np.array([np.pi - (2 * np.pi / planet_period) * days_since_start])
        r_planet = self.a_planet * (1 - self.e_planet**2) / (1 + self.e_planet * np.cos(theta_planet))
        x_planet = r_planet * np.cos(theta_planet)
        y_planet = r_planet * np.sin(theta_planet)
        
        # Keep planet position
        self.planet_theta[date] = theta_planet
        self.planet_x[date] = x_planet
        self.planet_y[date] = y_planet

        ###################
        # Earth positions #
        ###################

        # get ra/dec of the Sun and the target planet
        indexs = get_date_indexs(date, self.end_date, planet_period, self.data["Date"])
        sun_ra = self.data.loc[indexs, "Sun_RA"].values
        sun_dec = self.data.loc[indexs, "Sun_Dec"].values
        planet_ra = self.data.loc[indexs, f"{self.selected_planet}_RA"].values
        planet_dec = self.data.loc[indexs, f"{self.selected_planet}_Dec"].values
        # Convert RA and Dec to radians
        sun_ra = np.deg2rad(sun_ra)
        sun_dec = np.deg2rad(sun_dec)
        planet_ra = np.deg2rad(planet_ra)
        planet_dec = np.deg2rad(planet_dec)
        
        # Solve the triangle formed by the Sun, Earth, and the target planet
        #  TODO: maybe change with r_planet and r_earth
        theta_earth = find_theta_earth(
            sun_ra, sun_dec, planet_ra, planet_dec, self.a_earth, self.a_planet, 
            planet_period, earth_period)
        
        """earth_angle = angular_separation(sun_ra, sun_dec, planet_ra, planet_dec) # distance between measured angles
        # TODO: maybe change with r_planet and r_earth
        planet_angle = np.asin(self.a_earth/self.a_planet * np.sin(earth_angle)) # law of sines
        planet_angle_alt = np.pi - planet_angle
        sun_angle = find_sun_angle(earth_angle, planet_angle, planet_angle_alt)

        sun_angle = np.pi - earth_angle - planet_angle
        sun_angle = np.mod(sun_angle, 2 * np.pi)
        sun_angle_alt = np.pi - earth_angle - planet_angle_alt
        sun_angle_alt = np.mod(sun_angle_alt, 2 * np.pi)
        
        print("######################################################") 
        print("Sun sun_alt pred pred_alt")
        #circular_angle = np.array([
        #    sun_angle[0] + planet_period * index / earth_period * 2 * np.pi
        #    for index in range(len(indexs))
        #])
        circular_angle = np.array([
            sun_angle[index - 1] + planet_period / earth_period * 2 * np.pi
            if index > 0 else sun_angle[0]
            for index in range(sun_angle.shape[0] + 1)
        ])
        circular_angle = np.mod(circular_angle, 2 * np.pi)
        #circular_angle_alt = np.array([
        #    sun_angle_alt[0] + planet_period * index / earth_period * 2 * np.pi
        #    for index in range(len(indexs))
        #])
        circular_angle_alt = np.array([
            sun_angle_alt[index - 1] + planet_period / earth_period * 2 * np.pi
            if index > 0 else sun_angle_alt[0]
            for index in range(sun_angle.shape[0] + 1)
        ])
        circular_angle_alt = np.mod(circular_angle_alt, 2 * np.pi)
        
        for i1, i2, i3, i4 in zip(sun_angle, sun_angle_alt, circular_angle, circular_angle_alt):
            print(f"{i1/np.pi:.2f} {i2/np.pi:.2f} {i3/np.pi:.2f} {i4/np.pi:.2f}")

        print("######################################################")
        """

        # Assuming Earth and Mars are coplanar and Dec is 0
        #theta_earth = np.pi - earth_angle
        r_earth = self.a_earth * (1 - self.e_earth**2) / (1 + self.e_earth * np.cos(theta_earth))
        earth_x = r_earth * np.cos(theta_earth)
        earth_y = r_earth * np.sin(theta_earth)
        

        # Keep Earth position 
        self.earth_theta[date] = theta_earth # Earth angle with respect to Sun
        self.earth_x[date] = earth_x
        self.earth_y[date] = earth_y
    
