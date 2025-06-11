"""Define utility functions for the planet_orbits package."""
import numpy as np

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

def find_theta_earth(sun_ra, sun_dec, planet_ra, planet_dec, r_earth, r_planet, planet_period, earth_period, theta_planet):
    """
    Solve the triangle formed by the Sun, Earth, and the target planet. 
    Compute the angle theta_earth, which is the angular separation between Earth and the target planet.
    
    Arguments
    ---------
    sun_ra: float
    Right ascension of the Sun in radians.
    
    sun_dec: float
    Declination of the Sun in radians.
    
    planet_ra: float
    Right ascension of the target planet in radians.
    
    planet_dec: float
    Declination of the target planet in radians.
    
    r_earth: float
    Distance from the Sun to Earth in AU.
    
    r_planet: float
    Distance from the Sun to the target planet in AU.
    
    planet_period: float
    Orbital period of the target planet in days.

    earth_period: float
    Orbital period of Earth in days.

    theta_planet: float
    Angular position of the target planet in radians, relative to the Sun.

    Returns
    -------
    theta_sun: float 
    Angular separation between Earth and the target planet in radians.
    """    
    # distance between measured angles at the earth vertex of the Earth-planet-Sun triangle
    theta_earth = angular_separation(sun_ra, sun_dec, planet_ra, planet_dec)
    
    # use the law of sines to find the angle at the Earth vertex
    # there are two possible angles, for now we keep them both
    theta_planet1 = np.asin(r_earth/r_planet * np.sin(theta_earth)) # law of sines
    theta_planet2 = np.pi - theta_planet1  # the other angle
    aux_theta_sun1 = np.mod(np.pi - theta_earth - theta_planet1, 2 * np.pi)
    aux_theta_sun2 = np.mod(np.pi - theta_earth - theta_planet2, 2 * np.pi)
    
    # Adjust the angles to be relative to the planet's position
    aux_theta_sun1 = np.mod(aux_theta_sun1 + theta_planet, 2 * np.pi)
    aux_theta_sun2 = np.mod(aux_theta_sun2 + theta_planet, 2 * np.pi)
    #aux_theta_sun1 = np.mod(theta_earth + theta_planet, 2 * np.pi)
    #aux_theta_sun2 = np.mod(-theta_earth + theta_planet, 2 * np.pi)

    # To select the correct angle, we compare the difference between the measured angles 
    # and the simplified approximation of constant angle growth (assuming circular orbits) 
    # We do this twice, once for each starting angle, and we keep the one that has smaller 
    # overall difference.
    predicted_increase = planet_period / earth_period * 2 * np.pi

    theta_sun_option1 = np.zeros_like(theta_earth)
    theta_sun_option1[0] = aux_theta_sun1[0]
    diff1 = 0.0
    for index, (aux_theta1, aux_theta2) in enumerate(zip(aux_theta_sun1[1:], aux_theta_sun2[1:]), start=1):
        prediction = np.mod(theta_sun_option1[index - 1] + predicted_increase, 2 * np.pi)

        distances = np.array([
            angular_distance(aux_theta1, prediction),
            angular_distance(aux_theta2, prediction)
        ])
        angles = np.array([aux_theta1, aux_theta2])
        pos = np.argmin(distances)
        theta_sun_option1[index] = angles[pos]
        diff1 += distances[pos]

    theta_sun_option2 = np.zeros_like(theta_earth)
    theta_sun_option2[0] = aux_theta_sun2[0]
    diff2 = 0.0
    for index, (aux_theta1, aux_theta2) in enumerate(zip(aux_theta_sun1[1:], aux_theta_sun2[1:]), start=1):
        prediction = np.mod(theta_sun_option2[index - 1] + predicted_increase, 2 * np.pi)

        distances = np.array([
            angular_distance(aux_theta1, prediction),
            angular_distance(aux_theta2, prediction)
        ])
        angles = np.array([aux_theta1, aux_theta2])
        pos = np.argmin(distances)
        theta_sun_option2[index] = angles[pos]
        diff2 += distances[pos]

    # Select the option with the smallest difference
    if diff1 < diff2:
        theta_sun = theta_sun_option1
    else:
        theta_sun = theta_sun_option2

    # Adjust the angle to be relative to the planet's position
    return theta_sun
     
def get_date_indexs(start_date_str, end_date_str, date_step, date_list):
    """
    Get the date indexs for the given start and end dates with a specified step (period).
    
    Arguments
    ---------
    start_date_str: str
    Start date in 'YYYY-MM-DD' format.
    
    end_date_str: str
    End date in 'YYYY-MM-DD' format.
    
    date_step: int
    Step size in days.
    
    date_list: pd.Series
    List of dates in 'YYYY-MM-DD' format to search for the indexs.

    Returns
    -------
    dates: list of str
    List of dates from start to end with the specified step.
    """
    # Convert start_date and end_date to datetime objects
    start_date = np.datetime64(start_date_str)
    end_date = np.datetime64(end_date_str)
    
    # Generate the date range with the specified step
    dates = np.arange(start_date, end_date + np.timedelta64(1, 'D'), np.timedelta64(date_step, 'D'))
    
    # Find indexs in the date_list
    indexs = [np.where(date_list == str(date))[0] for date in dates] 
    
    return np.array(indexs).flatten()