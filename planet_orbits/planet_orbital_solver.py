"""Define the PlanetOrbitalSolver class to handle planet coordinates in a 
solar system simulation."""
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.optimize import minimize_scalar

from planet_orbits.errors import PlanetOrbitalSolverError
from planet_orbits.utils import add_ecliptic_coordinates, angular_separation, orbital_radius, solve_triangle

# Angular tolerance for finding oppositions (in radians)
ANGULAR_TOLERANCE_RADIANS = np.radians(10)  # 10 degrees
 

# Number of model points to compute
N_MODEL_POINTS = 1000

# periods of planets in Earth days
# currently based on data from https://en.wikipedia.org/wiki/Solar_System
PLANET_PERIODS = {
    "mercury": 87.969,
    "venus": 224.701,
    "earth": 365.256,
    "mars": 686.980, # I also found this value with higher precision (not sure where from, need to double-check): 686.97959
    "jupiter": 4332.589,
    "saturn": 10759.22,
    "uranus": 30688.5,
    "neptune": 60182.0,
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

        print("Loaded data")
        print(self.data.iloc[::24])

        self.available_planets = [
            col.split("_")[0]
            for col in self.data.columns
            if col.endswith("_ra") and col.split("_")[0] != "sun"
        ]

        self.data = add_ecliptic_coordinates(self.data, names=["sun"] + self.available_planets)

        print("Added ecliptic coordinates")
        print(self.data.iloc[::24])


        self.selected_planet = None

        # Placeholder for the period of the selected planet, to be set when a planet is selected
        self.planet_period = None # in days
        self.earth_period = PLANET_PERIODS["earth"] # in days

        # Placeholder for the opposition dates of the selected planet, to be computed when a planet is selected
        self.data_oppositions = None
        self.data_oppositions_series = []
        self.data_oppositions_series_plot = []

        # Placeholder for the orbital parameters of the selected planet, to be set when a planet is selected
        self.planet_semimajor_axis = None # semi-major axis of the selected planet in AU
        self.planet_eccentricity = None # eccentricity of the selected planet
        self.planet_phase = None # phase of the first date in the selected planet in radians (with respect to the periastsron)
        self.earth_semimajor_axis = 1.0 # semi-major axis of the Earth in AU
        self.earth_eccentricity = 0.0167 # eccentricity of the Earth
        self.earth_phase = 0.0 # phase of the first date in Earth in radians (with respect to the periastsron)

        # Initialize lists to store positions
        # Positions are stored as np.arrays for date group
        # Date groups are defined by dates at which the target planet is in the 
        # same position, determined by the period of the planet
        # keys are the first date of the group
        self.earth_coordinates = {}
        self.planet_coordinates = {}
        self.sun_coordinates = (0, 0)

        # Initialize metrics
        self.metrics = {}
        self.total_dispersion = 0.0
        self.total_chi2 = 0.0
        self.total_points = 0
        
        # Initialize model positions
        self.model_time = None
        self.model_planet = None
        self.model_earth = None

    def compute_orbital_models(self):
        """Compute the theoretical orbital models for the selected planet and Earth based on their orbital parameters."""
        if self.selected_planet is None:
            raise PlanetOrbitalSolverError("No planet selected.")

        theta = np.linspace(0, 2*np.pi, N_MODEL_POINTS)

        #######################
        # target planet model #
        #######################
        planet_r = orbital_radius(
            self.planet_semimajor_axis, self.planet_eccentricity, theta, self.planet_phase)
        self.model_planet = (
            planet_r * np.cos(theta),
            planet_r * np.sin(theta)
        )

        ###############
        # Earth model #
        ###############
        earth_r = orbital_radius(
            self.earth_semimajor_axis, self.earth_eccentricity, theta, self.earth_phase)
        self.model_earth = (
            earth_r * np.cos(theta),
            earth_r * np.sin(theta)
        )

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
        """
        angle_sun_planet = angular_separation(
            np.radians(self.data["sun_ra"].values),
            np.radians(self.data["sun_dec"].values),
            np.radians(self.data[f"{self.selected_planet}_ra"].values),
            np.radians(self.data[f"{self.selected_planet}_dec"].values)
        )
        diff = np.pi - angle_sun_planet
        """
        sun_lon_anti = (self.data["sun_lon"] + 180) % 360
        diff = np.radians(np.fabs(sun_lon_anti - self.data[f"{self.selected_planet}_lon"].values))
        opposition_indices = np.where(np.isclose(diff, 0, atol=ANGULAR_TOLERANCE_RADIANS))[0]
        
        """
        cols = ["date", "sun_ra", "sun_dec", f"{self.selected_planet}_ra", f"{self.selected_planet}_dec"]
        """
        cols = ["date", "sun_lon", f"{self.selected_planet}_lon"]
        df_aux = self.data.iloc[opposition_indices][cols].copy()#.reset_index(drop=True)
        """
        df_aux["angle_sun_planet"] = np.degrees(angle_sun_planet[opposition_indices])
        """
        df_aux["delta_angle"] = np.degrees(diff[opposition_indices])
        
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
            """
            cs_sun_ra = CubicSpline(delta_times, group["sun_ra"])
            cs_sun_dec = CubicSpline(delta_times, group["sun_dec"])
            cs_planet_ra = CubicSpline(delta_times, group[f"{self.selected_planet}_ra"])
            cs_planet_dec = CubicSpline(delta_times, group[f"{self.selected_planet}_dec"])

            sun_ra = cs_sun_ra(delta_time_min_spline)
            sun_dec = cs_sun_dec(delta_time_min_spline)  
            planet_ra = cs_planet_ra(delta_time_min_spline)
            planet_dec = cs_planet_dec(delta_time_min_spline)
            #angle_sun_planet = angular_separation(
            #    np.radians(sun_ra), np.radians(sun_dec), np.radians(planet_ra), np.radians(planet_dec))
            """
            cs_sun_lon = CubicSpline(delta_times, group["sun_lon"])
            cs_planet_lon = CubicSpline(delta_times, group[f"{self.selected_planet}_lon"]) 

            interp_sun_lon = cs_sun_lon(delta_time_min_spline)
            interp_sun_lon_anti = (interp_sun_lon + 180) % 360
            interp_planet_lon = cs_planet_lon(delta_time_min_spline)
            interp_diff = np.fabs(interp_sun_lon_anti - interp_planet_lon)

            """
            opposition_row = {
                "date": date_min_spline,
                "sun_ra": sun_ra,
                "sun_dec": sun_dec,
                f"{self.selected_planet}_ra": planet_ra,
                f"{self.selected_planet}_dec": planet_dec,
                #"angle_sun_planet": np.degrees(angle_sun_planet),
                #"delta_angle": np.degrees(np.pi - angle_sun_planet)

            }
            """

            opposition_row = {
                "date": date_min_spline,
                "sun_lon": interp_sun_lon,
                f"{self.selected_planet}_lon": interp_planet_lon,
                #"angle_sun_planet": np.degrees(interp_diff),
                "delta_angle": interp_diff,
            }

            opposition_rows.append(opposition_row)

        self.data_oppositions = pd.DataFrame(opposition_rows)

        print("Found oppositions:")
        print(self.data_oppositions)

        print("\n")
        t_syn_calc = self.data_oppositions["date"].diff().dt.days.mean()
        # Outer planet synodic equation: 1/T_syn = 1/T_earth − 1/T_sid
        t_sid_calc = 1.0 / ((1.0 / PLANET_PERIODS.get("earth")) - (1.0 / t_syn_calc))
        print(f"Synodic period  (T_syn)  for {self.selected_planet}: {t_syn_calc}")
        print(f"Sidereal period (T_sid) for {self.selected_planet}: {t_sid_calc}")

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

        # otherwise compute the yearly series for each opposition date
        series_lengths = []
        for index in range(self.data_oppositions.shape[0]):
            initial_date = self.data_oppositions.loc[index, "date"]

            period_in_seconds = self.planet_period*24*3600

            series_length = round(
                (self.data.loc[self.data.shape[0]-1, "date"] - initial_date).total_seconds() / period_in_seconds
            )
            series_lengths.append(series_length)
            
            series_rows = []
            """
            series_rows.append({
                "date": self.data_oppositions.loc[index, "date"],
                "sun_ra": np.float64(self.data_oppositions.loc[index, "sun_ra"]),
                "sun_dec": np.float64(self.data_oppositions.loc[index, "sun_dec"]),
                f"{self.selected_planet}_ra": np.float64(self.data_oppositions.loc[index, f"{self.selected_planet}_ra"]),
                f"{self.selected_planet}_dec": np.float64(self.data_oppositions.loc[index, f"{self.selected_planet}_dec"]),
                "angle_sun_planet": np.float64(self.data_oppositions.loc[index, "angle_sun_planet"]),
                #"delta_angle": np.float64(self.data_oppositions.loc[index, "delta_angle"]),
            })
            """
            series_rows.append({
                "date": self.data_oppositions.loc[index, "date"],
                "sun_lon": np.float64(self.data_oppositions.loc[index, "sun_lon"]),
                f"{self.selected_planet}_lon": np.float64(self.data_oppositions.loc[index, f"{self.selected_planet}_lon"]),
            })

            for index2 in range(1, series_length):
                current_date = initial_date + pd.Timedelta(seconds=round(index2*period_in_seconds))

                # select some dates around current_date to interpolate the coordinates
                dates_around_current_date = self.data[
                    (self.data["date"] > current_date - pd.Timedelta(hours=10)) & 
                    (self.data["date"] < current_date + pd.Timedelta(hours=10))]
                
                delta_times = (dates_around_current_date["date"] - current_date).dt.total_seconds()
                """
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
                    "sun_ra": np.float64(sun_ra),
                    "sun_dec": np.float64(sun_dec),
                    f"{self.selected_planet}_ra": np.float64(planet_ra),
                    f"{self.selected_planet}_dec": np.float64(planet_dec),
                    "angle_sun_planet": np.nan
                }
                """
                cs_sun_lon = CubicSpline(delta_times, dates_around_current_date["sun_lon"])
                cs_planet_lon = CubicSpline(delta_times, dates_around_current_date[f"{self.selected_planet}_lon"])

                interp_sun_lon = cs_sun_lon(0.0)
                interp_planet_lon = cs_planet_lon(0.0)
                series_row = {
                    "date": current_date,
                    "sun_lon": np.float64(interp_sun_lon),
                    f"{self.selected_planet}_lon": np.float64(interp_planet_lon),
                }
                series_rows.append(series_row)

            series_data = pd.DataFrame(series_rows)

            series_data = solve_triangle(series_data, self.selected_planet)
            
            self.data_oppositions_series.append(series_data)

            if index == 0:
                print("Found series of yearly positions for the first opposition:")
                print(series_data)

        # setup plotting flags for the series
        # default is to plot all the series, but the user can select which ones to plot in the UI
        self.data_oppositions_series_plot = [True]*len(self.data_oppositions_series)
    
        return series_lengths, self.data_oppositions_series_plot
    
    def find_planet_coordinates(self):
        """Find the coordinates of the planets for each date in the data.
        
        Returns
        -------
        coordinates: dict
        Dictionary containing the coordinates of the planets for each date in the data.

        Raises
        ------
        PlanetOrbitalSolverError if no planet is selected or if no oppositions series are found.
        """
        if self.selected_planet is None:
            raise PlanetOrbitalSolverError("No planet selected.")
        if len(self.data_oppositions_series) == 0:
            raise PlanetOrbitalSolverError("No oppositions series found. Please run find_oppositions_series() first.")

        # Rebuild coordinates from scratch so deselected series are removed from the plot.
        self.earth_coordinates = {}
        self.planet_coordinates = {}
        self.metrics = {}
        self.total_dispersion = 0.0
        self.total_chi2 = 0.0
        self.total_points = 0
        
        for data_oppositions_series, data_oppositions_series_plot in zip(self.data_oppositions_series, self.data_oppositions_series_plot):
            if not data_oppositions_series_plot:
                continue

            # Earth-Sun distance
            earth_lon_heliocentric = np.radians((data_oppositions_series["sun_lon"].values + 180) % 360)
            earth_sun_distance = orbital_radius(
                self.earth_semimajor_axis, self.earth_eccentricity, earth_lon_heliocentric, self.earth_phase)
            data_oppositions_series["earth_r"] = earth_sun_distance
            
            # Planet-Sun distance
            angle_at_earth = np.radians(data_oppositions_series["angle_at_earth"])
            angle_at_planet = np.radians(data_oppositions_series[f"angle_at_{self.selected_planet}"])
            planet_sun_distance = earth_sun_distance * np.sin(angle_at_earth) / np.sin(angle_at_planet)
            planet_lon_heliocentric = np.radians((data_oppositions_series["sun_lon"].values[0] + 180) % 360)


            print("Finding planet coordinates")
            for date, earth_r, planet_r in zip(data_oppositions_series["date"], earth_sun_distance, planet_sun_distance):
                print(f"Date: {date}, Earth-Sun distance: {earth_r:.5f} AU, Planet-Sun distance: {planet_r:.5f} AU")

            # skip the first date of the series, as it serves as anchor and the triangulation is not valid
            earth_sun_distance = earth_sun_distance[1:]
            earth_lon_heliocentric = earth_lon_heliocentric[1:]
            planet_sun_distance = planet_sun_distance[1:]
            #planet_lon_heliocentric = planet_lon_heliocentric[1:]

            # store the cartesian coordinates for the plot
            self.earth_coordinates[data_oppositions_series["date"].iloc[0]] = (
                earth_sun_distance * np.cos(earth_lon_heliocentric),
                earth_sun_distance * np.sin(earth_lon_heliocentric))
            self.planet_coordinates[data_oppositions_series["date"].iloc[0]] = (
                planet_sun_distance * np.cos(planet_lon_heliocentric),
                planet_sun_distance * np.sin(planet_lon_heliocentric),
            )

            ##########################################
            # compute per-series performance metrics #
            ##########################################

            # keep the dispersion values for the series to show in the table in the UI
            mean = np.mean(planet_sun_distance)
            num_points = planet_sun_distance.shape[0]
            self.total_points += num_points
            self.total_dispersion += np.sum((planet_sun_distance - mean)**2)
            
            # keep the chi2 values for the series to show in the table in the UI
            predicted_planet_sun_distance = orbital_radius(
                self.planet_semimajor_axis, self.planet_eccentricity, planet_lon_heliocentric, self.planet_phase)
            chi2 = np.sum((planet_sun_distance - predicted_planet_sun_distance)**2)
            self.total_chi2 += chi2

            self.metrics[data_oppositions_series["date"].iloc[0]] = (
                np.std(planet_sun_distance),
                chi2,
                num_points,
            )

        self.total_dispersion = np.sqrt(self.total_dispersion / self.total_points) if self.total_points > 0 else 0.0


    def reset_planet(self):
        """
        Reset the selected planet and its properties.
        
        This method clears the selected planet, resets the orbital parameters, 
        and clears any stored opposition data.
        """

        self.selected_planet = None

        # reset periods
        self.planet_period = None
        self.earth_period = PLANET_PERIODS["earth"]

        # reset opposition data
        self.reset_opposition_data()

        # reset orbital parameters
        self.reset_orbital_parameters()

    def reset_opposition_data(self):
        """
        Reset the opposition data for the selected planet.
        
        This method clears any stored opposition data, including the dates of oppositions 
        and the series of yearly positions based on those oppositions.
        """
        self.data_oppositions = None
        self.data_oppositions_series = []
        self.data_oppositions_series_plot = []

    def reset_orbital_parameters(self):
        """
        Reset the orbital parameters of the selected planet to default values.
        
        This method sets the semi-major axis, eccentricity, and phase of the selected planet 
        to their default values based on the known parameters of the planets in our solar system.
        """
        if self.selected_planet is None:
            self.planet_semimajor_axis = None
            self.planet_eccentricity = None
            self.planet_phase = None
        elif self.selected_planet in ["mercury", "venus"]:
            self.planet_semimajor_axis = 0.5 # in AU
            self.planet_eccentricity = 0.0
            self.planet_phase = 0.0  # in radians
        else:
            self.planet_semimajor_axis = 1.5 # in AU
            self.planet_eccentricity = 0.0
            self.planet_phase = 0.0 # in radians

        self.earth_semimajor_axis = 1.0
        self.earth_eccentricity = 0.0 # 0.0167
        self.earth_phase = 0.0 # in radians

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
        if planet_name not in self.available_planets and planet_name is not None:
            raise PlanetOrbitalSolverError(
                f"Invalid planet name: {planet_name}. Available planets: {self.available_planets}")

        # Reset the active dates if changing the planet
        if self.selected_planet is None or self.selected_planet != planet_name:
            self.reset_planet()

        self.selected_planet = planet_name
        if self.selected_planet is not None:
            # update the period of the selected planet
            self.planet_period = PLANET_PERIODS[self.selected_planet] # in days

            # update orbital parameters of the selected planet
            self.reset_orbital_parameters()
