"""Define the PlanetOrbitalSolver class to handle planet coordinates in a 
solar system simulation."""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.optimize import minimize_scalar

from planet_orbits.errors import PlanetOrbitalSolverError
#from planet_orbits.utils import find_theta_earth, get_date_indexs
from planet_orbits.utils import angular_separation

# Angular tolerance for finding oppositions (in radians)
ANGULAR_TOLERANCE_RADIANS = np.radians(10)  # 10 degrees

# Number of model points to compute
N_MODEL_POINTS = 1000

# periods of planets in Earth days
PLANET_PERIODS = {
    "mercury": 88,
    "venus": 225,
    "earth": 365,
    "mars": 687,
    "jupiter": 4333,
    "saturn": 10759,
    "uranus": 30687,
    "neptune": 60190,
}

class PlanetOrbitalSolver:
    """
    Class to handle the coordinates of planets in a solar system simulation.
    """
    def __init__(self, filename):
        """
        Initialize the PlanetOrbitalSolver class.

        Arguments
        ---------
        filename: str
        Path to the CSV file containing planet data.
        """
        self.filename = filename
        self.data = pd.read_csv(filename, parse_dates=["date"])

        self.available_planets = [
            col.split("_")[0]
            for col in self.data.columns
            if col.endswith("_ra") and col.split("_")[0] != "sun"
        ]

        self.selected_planet = None

        # Placeholder for the period of the selected planet, to be set when a planet is selected
        self.planet_period = None # in days
        self.earth_period = PLANET_PERIODS["earth"] # in days

        # Placeholder for the opposition dates of the selected planet, to be computed when a planet is selected
        self.data_oppositions = None
        self.data_oppositions_series = []
        self.data_oppositions_series_plot = []

        """Old code

        self.planet_a = None # semi-major axis of the selected planet in AU
        self.planet_e = 0 # eccentricity of the selected planet
        
        self.earth_a = 1.0
        self.earth_e = 0
        self.earth_phase = 0.0
        
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
        """

    def find_oppositions(self):
        """
        Find the dates of oppositions for the selected planet. 

        Store the oppositions in the data_oppositions attribute

        Returns
        -------
        opposition_dates: pd.Series
        List of opposition dates

        Raises
        ------
        PlanetOrbitalSolverError if no planet is selected.
        """
        if self.selected_planet is None:
            raise PlanetOrbitalSolverError("No planet selected.")

        # Find the dates of oppositions using the data
        angle_sun_planet = angular_separation(
            np.radians(self.data["sun_ra"].values),
            np.radians(self.data["sun_dec"].values),
            np.radians(self.data[f"{self.selected_planet}_ra"].values),
            np.radians(self.data[f"{self.selected_planet}_dec"].values)
        )
        diff = np.pi - angle_sun_planet
        opposition_indices = np.where(np.isclose(diff, 0, atol=ANGULAR_TOLERANCE_RADIANS))[0]
        
        cols = ["date", "sun_ra", "sun_dec", f"{self.selected_planet}_ra", f"{self.selected_planet}_dec"]
        df_aux = self.data.iloc[opposition_indices][cols].copy().reset_index(drop=True)
        df_aux["angle_sun_planet"] = np.degrees(angle_sun_planet[opposition_indices])
        df_aux["delta_angle"] = (diff[opposition_indices])

        consecutive_groups = (df_aux["date"].diff() != pd.Timedelta(hours=1)).cumsum()
        opposition_rows = []
        for _, group in df_aux.groupby(consecutive_groups):
            delta_times = (group["date"] - group["date"].iloc[0]).dt.total_seconds()
            # Minimize the delta_angle values to find the best estimate of the opposition time within this group.
            # Use cubic spline interpolation to find a more accurate estimate of the opposition time.
            cs_delta_angle = CubicSpline(delta_times, group["delta_angle"])
            result = minimize_scalar(cs_delta_angle, bounds=(delta_times.min(), delta_times.max()), method='bounded')
            delta_time_min_spline = result.x
            date_min_spline = group["date"].iloc[0] + pd.to_timedelta(delta_time_min_spline, unit="s")

            # now that we have the estimated time, use a cubic interpolation to find the corresponding coordinates 
            cs_sun_ra = CubicSpline(delta_times, group["sun_ra"])
            cs_sun_dec = CubicSpline(delta_times, group["sun_dec"])
            cs_planet_ra = CubicSpline(delta_times, group[f"{self.selected_planet}_ra"])
            cs_planet_dec = CubicSpline(delta_times, group[f"{self.selected_planet}_dec"])

            sun_ra = cs_sun_ra(delta_time_min_spline)
            sun_dec = cs_sun_dec(delta_time_min_spline)  
            planet_ra = cs_planet_ra(delta_time_min_spline)
            planet_dec = cs_planet_dec(delta_time_min_spline)
            angle_sun_planet = angular_separation(
                np.radians(sun_ra), np.radians(sun_dec), np.radians(planet_ra), np.radians(planet_dec))

            opposition_row = {
                "date": date_min_spline,
                "sun_ra": sun_ra,
                "sun_dec": sun_dec,
                f"{self.selected_planet}_ra": planet_ra,
                f"{self.selected_planet}_dec": planet_dec,
                "angle_sun_planet": np.degrees(angle_sun_planet),
                "delta_angle": np.degrees(np.pi - angle_sun_planet)

            }

            opposition_rows.append(opposition_row)

        self.data_oppositions = pd.DataFrame(opposition_rows)
        
        return self.data_oppositions["date"]
    
    def find_oppositions_series(self):
        """Find the series of yearly positions based on the oppositions found for the selected planet.
        
        Returns
        -------
        series_lengths: list of int
        List of lengths of the series of yearly positions for each opposition date.

        Raises
        ------
        PlanetOrbitalSolverError if no oppositions are found.
        """
        if self.data_oppositions is None:
            raise PlanetOrbitalSolverError("No oppositions found. Please run find_oppositions() first.")

        # if series are already computed, return the lengths of the series
        if len(self.data_oppositions_series) > 0:
            series_lengths = [series.shape[0] for series in self.data_oppositions_series]
            return series_lengths, self.data_oppositions_series_plot

        # otherwiser compute the yearly series for each opposition date
        series_lengths = []
        for index in range(self.data_oppositions.shape[0]):
            initial_date = self.data_oppositions.loc[index, "date"]

            period_in_seconds = self.planet_period*24*3600

            series_length = round(
                (self.data.loc[self.data.shape[0]-1, "date"] - initial_date).total_seconds() / period_in_seconds
            )
            series_lengths.append(series_length)
            
            series_rows = []
            series_rows.append({
                "date": self.data_oppositions.loc[index, "date"],
                "sun_ra": self.data_oppositions.loc[index, "sun_ra"],
                "sun_dec": self.data_oppositions.loc[index, "sun_dec"],
                f"{self.selected_planet}_ra": self.data_oppositions.loc[index, f"{self.selected_planet}_ra"],
                f"{self.selected_planet}_dec": self.data_oppositions.loc[index, f"{self.selected_planet}_dec"],
                "angle_sun_planet": self.data_oppositions.loc[index, "angle_sun_planet"],
                "delta_angle": self.data_oppositions.loc[index, "delta_angle"],
            })

            for index in range(1, series_length):
                current_date = initial_date + pd.Timedelta(seconds=round(index*period_in_seconds))

                # select some dates around date2 to interpolate the coordinates
                dates_around_current_date = self.data[
                    (self.data["date"] > current_date - pd.Timedelta(hours=10)) & 
                    (self.data["date"] < current_date + pd.Timedelta(hours=10))]
                
                delta_times = (dates_around_current_date["date"] - current_date).dt.total_seconds()
                cs_sun_ra = CubicSpline(delta_times, dates_around_current_date["sun_ra"])
                cs_sun_dec = CubicSpline(delta_times, dates_around_current_date["sun_dec"])
                cs_planet_ra = CubicSpline(delta_times, dates_around_current_date[f"{self.selected_planet}_ra"])
                cs_planet_dec = CubicSpline(delta_times, dates_around_current_date[f"{self.selected_planet}_dec"])

                sun_ra = cs_sun_ra(0.0)
                sun_dec = cs_sun_dec(0.0)  
                planet_ra = cs_planet_ra(0.0)
                planet_dec = cs_planet_dec(0.0)
                
                series_row = {
                    "date": current_date,
                    "sun_ra": sun_ra,
                    "sun_dec": sun_dec,
                    f"{self.selected_planet}_ra": planet_ra,
                    f"{self.selected_planet}_dec": planet_dec,
                }

                series_rows.append(series_row)

            series_data = pd.DataFrame(series_rows)
            self.data_oppositions_series.append(series_data)

        # setup plotting flags for the series
        # default is to plot all the series, but the user can select which ones to plot in the UI
        self.data_oppositions_series_plot = [True]*len(self.data_oppositions_series)
    
        return series_lengths, self.data_oppositions_series_plot

    def reset_planet(self, planet_name):
        """
        Reset the selected planet and its properties.

        Arguments
        ---------
        planet_name: str
        Name of the planet to be reset.
        """

        self.selected_planet = None

        # reset periods
        self.planet_period = None
        self.earth_period = PLANET_PERIODS["earth"]

        # reset opposition data
        self.data_oppositions = None
        self.data_oppositions_series = []
        self.data_oppositions_series_plot = []
        """Old code
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
        """

    def set_selected_planet(self, planet_name):
        """
        Set the selected planet for the simulation.

        Arguments
        ---------
        planet_name: str
        Name of the planet to be selected.

        Raise
        -----
        PlanetOrbitalSolverError if no valid planet is selected.
        """
        if planet_name not in self.available_planets:
            raise PlanetOrbitalSolverError(
                f"Invalid planet name: {planet_name}. Available planets: {self.available_planets}")

        # Reset the active dates if changing the planet
        if self.selected_planet is None or self.selected_planet != planet_name:
            self.reset_planet(planet_name)

        self.selected_planet = planet_name
        if self.selected_planet is not None:
           # update the period of the selected planet
           self.planet_period = PLANET_PERIODS[self.selected_planet] # in days
           
           """Old code
           self.set_planet_positions(self.dates[0])
           self.set_model_positions()
           """

    def set_model_positions(self):
        """
        Compute the theoretical positions of the planets given the 
        selected planetary orbit parameters.
        Store them in the respective dictionaries.

        Raise
        -----
        PlanetOrbitalSolverError if no planet is selected.
        """
        if self.selected_planet is None:
            raise PlanetOrbitalSolverError("No planet selected.")

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
        PlanetOrbitalSolverError if no planet is selected or if the date is not in the data.
        """
        if self.selected_planet is None:
            raise PlanetOrbitalSolverError("No planet selected.")

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
        