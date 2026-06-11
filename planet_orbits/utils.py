"""Define utility functions for the planet_orbits package."""
import numpy as np

# Ecliptic plane inclination 
# Accurate value for J2000 coordinates (https://ui.adsabs.harvard.edu/abs/2000eaa..bookE4946./abstract) 
EPSILON = np.radians(23 + 26/60 + 21/3600)


def add_ecliptic_coordinates(df, names):
    """Add ecliptic longitude columns to the DataFrame for the Sun and planets.
    
    Arguments
    ---------
    df: pandas.DataFrame
    DataFrame containing columns '{name}_ra', '{name}_dec' for each name in the list.
    Angles in these columns should be in degrees.

    names: list of str
    List of names (e.g., ['sun', 'mars', 'jupiter']) to specify which columns to process. 
    The function will look for columns '{name}_ra' and '{name_dec}' for each name in the list.

    Returns
    -------
    df: pandas.DataFrame
    The input DataFrame with additional columns for ecliptic longitudes, named '{name}_lon' for each name in the input list.
    Angles will be in degrees in the output columns.
    """
    for name in names:
        if f"{name}_ra" not in df.columns or f"{name}_dec" not in df.columns:
            raise ValueError(f"DataFrame must contain columns '{name}_ra' and '{name}_dec' for name '{name}'.")
        
        # TODO: figure out which to select for the final output
        # option 1: using equation 2.22 in Kartunen's Fundamental Astronomy (page 21)
        # option 2: using rotation matrixes
        # currently selecting option 2 for comparison with PEF2 code.

        # Using equation 2.22 in Kartunen's Fundamental Astronomy (page 21) to convert from equatorial to ecliptic coordinates
        ra = np.radians(df[f"{name}_ra"].values)
        dec = np.radians(df[f"{name}_dec"].values)
        sin_lam_cos_beta = np.sin(dec)*np.sin(EPSILON) + np.cos(dec)*np.cos(EPSILON)*np.sin(ra)
        cos_lam_cos_beta = np.cos(dec)*np.cos(EPSILON)*np.cos(ra)
        lon = np.arctan2(sin_lam_cos_beta, cos_lam_cos_beta)
        lon = np.mod(lon, 2 * np.pi)
        df[f"{name}_lon_alt"] = np.degrees(lon)

        # alternative using rotation matrixes
        # Unit vector in equatorial frame
        x_eq = np.cos(ra) * np.cos(dec)
        y_eq = np.sin(ra) * np.cos(dec)
        z_eq = np.sin(dec)

        # Rotate to ecliptic frame (x unchanged; rotate y-z plane by ε)
        x_ecl = x_eq
        y_ecl = np.cos(EPSILON) * y_eq + np.sin(EPSILON) * z_eq

        # Geocentric ecliptic longitude λ in [0°, 360°)
        lam = np.mod(np.arctan2(y_ecl, x_ecl), 2 * np.pi)
        df[f"{name}_lon"] = np.degrees(lam)

    return df

def angular_distance(angle1, angle2):
    """Return the minimal distance between two angles, result in [0, pi].
    
    Arguments
    ---------
    angle1: float
    First angle in radians.

    angle2: float
    Second angle in radians.

    Returns
    -------
    distance: float
    The angular distance between the two angles in radians, in the range [0, pi].
    """
    return np.abs(np.arctan2(np.sin(angle1 - angle2), np.cos(angle1 - angle2)))

def angular_separation(ra1, dec1, ra2, dec2):
    """
    Calculate the angular separation between two points on the celestial sphere.
    
    Arguments
    ---------
    ra1: float
    Right ascension of the first point in radians.

    dec1: float
    Declination of the first point in radians.

    ra2: float
    Right ascension of the second point in radians.
    
    dec2: float
    Declination of the second point in radians.
    
    Returns
    -------
    theta: float 
    Angular separation in radians.
    """
    # Calculate the angular separation using the spherical law of cosines
    cos_theta = (np.sin(dec1) * np.sin(dec2) +
                 np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2))
    
    # Ensure the value is within the valid range for arccos
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
    # Calculate the angle in radians
    theta = np.arccos(cos_theta)
    
    return theta

def orbital_radius(semi_major_axis, eccentricity, theta, phase):
    """Calculate the orbital radius of a planet.

    Arguments
    ---------
    semi_major_axis: float
    Semi-major axis of the planet's orbit in AU.

    eccentricity: float
    Eccentricity of the planet's orbit.

    theta: float
    True anomaly of the planet in radians.

    phase: float
    Phase angle of the planet in radians.

    Returns
    -------
    radius: float
    The orbital radius of the planet in AU.
    """
    return semi_major_axis * (1 - eccentricity**2) / (1 + eccentricity * np.cos(theta - phase))

def solve_triangle(series_data, planet_name):
    """Solve the triangle formed by the Sun, Earth, and Planet for each row in series_data.
    
    Arguments
    ---------
    series_data: pandas.DataFrame
    DataFrame containing the columns 'sun_ra', 'sun_dec', '{planet_name}_ra', '{planet_name}_dec'.

    planet_name: str
    Name of the planet (e.g., 'mars') to use for column names.

    Returns
    -------
    series_data: pandas.DataFrame
    The input DataFrame with additional columns for angles and distances.
    """
    sun_lon = np.radians(series_data["sun_lon"].values)
    planet_lon = np.radians(series_data[f"{planet_name}_lon"].values)

    # solve the triangle formed by the Sun, Earth, and the planet 
    # angle at Earth vertex
    aux = np.fabs(sun_lon - planet_lon)
    angle_at_earth = np.min([aux, 2*np.pi - aux], axis=0)
    series_data["angle_at_earth"] = np.degrees(angle_at_earth)

    # angle at Sun vertex
    aux = np.fabs(sun_lon[0] - sun_lon)
    angle_at_sun = np.min([aux, 2*np.pi - aux], axis=0)
    series_data["angle_at_sun"] = np.degrees(angle_at_sun)
    
    # angle at Planet vertex
    angle_at_planet = np.pi - angle_at_earth - angle_at_sun
    series_data[f"angle_at_{planet_name}"] = np.degrees(angle_at_planet)

    return series_data