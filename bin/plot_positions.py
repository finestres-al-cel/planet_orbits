import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def angular_separation(ra1, dec1, ra2, dec2):
    """
    Calculate the angular separation between two points on the celestial sphere.
    
    Parameters:
    ra1, dec1 : float
        Right ascension and declination of the first point in radians.
    ra2, dec2 : float
        Right ascension and declination of the second point in radians.
    
    Returns:
    float
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

def plot_positions(dates, sun_positions, earth_positions, mars_positions):
    plt.figure(figsize=(8, 8))
    
    # Plot the Sun's position
    plt.plot(0, 0, 'yo', label='Sun')
    
    # Plot the Earth's positions
    earth_x, earth_y = zip(*earth_positions)
    plt.plot(earth_x, earth_y, 'bo', label='Earth')
    
    # Plot the Mars' positions
    mars_x, mars_y = zip(*mars_positions)
    plt.plot(mars_x, mars_y, 'ro', label='Mars')
    
    plt.legend()
    plt.title(f'Positions from {dates[0]} to {dates[-1]}')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.grid(True)
    plt.axis('equal')
    plt.show()

def main(filename, start_date, end_date, date_step):
    # Read the data from the CSV file
    df = pd.read_csv(filename)

    # Convert start_date and end_date to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    dates = []
    sun_positions = []
    earth_positions = []
    mars_positions = []

    # Iterate over the date range
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        row = df[df['Date'] == date_str]
        if not row.empty:
            # Extract the RA and Dec values
            sun_ra = row['sun_RA'].values[0]
            sun_dec = row['sun_Dec'].values[0]
            mars_ra = row['mars_RA'].values[0]
            mars_dec = row['mars_Dec'].values[0]

            # Convert RA and Dec to radians
            sun_ra_rad = np.deg2rad(sun_ra)
            sun_dec_rad = np.deg2rad(sun_dec)
            mars_ra_rad = np.deg2rad(mars_ra)
            mars_dec_rad = np.deg2rad(mars_dec)

            # Size of Earth and Mars orbits in AU
            earth_orbit = 1
            mars_orbit = 1.52

            # Find angles for the Sun-Earth-Mars triangle
            earth_angle = angular_separation(sun_ra, sun_dec, mars_ra, mars_dec) # distance between measured angles
            mars_angle = np.asin(earth_orbit/mars_orbit * np.sin(earth_angle)) # law of sines
            sun_angle = np.pi - earth_angle - mars_angle

            # Assuming Earth and Mars are coplanar and Dec is 0
            earth_x = earth_orbit*np.cos(sun_angle)
            earth_y = earth_orbit*np.sin(sun_angle)
            mars_x = -mars_orbit
            mars_y = 0.0

            dates.append(date_str)
            sun_positions.append((0, 0))
            earth_positions.append((earth_x, earth_y))
            mars_positions.append((mars_x, mars_y))
        else:
            print(f"No data found for date {date_str}")

        # Increment the date by date_step days
        current_date += timedelta(days=date_step)

    # Plot all positions
    plot_positions(dates, sun_positions, earth_positions, mars_positions)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot positions of Earth, Mars, and the Sun.")
    parser.add_argument("filename", type=str, help="Input CSV file")
    parser.add_argument("start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("date_step", type=int, help="Step in days")
    
    args = parser.parse_args()
    main(args.filename, args.start_date, args.end_date, args.date_step)