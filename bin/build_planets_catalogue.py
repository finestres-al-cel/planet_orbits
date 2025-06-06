from astropy.time import Time
from astropy.coordinates import get_body, solar_system_ephemeris
import astropy.units as u
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def main(args):
    # Define time range
    dates = Time(np.arange(args.start_date, args.end_date, args.date_step, dtype="datetime64[D]"))

    # Planets of interest
    bodies = ["sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]

    # Dictionary to store the data
    data = {"Date": [date.strftime('%Y-%m-%d') for date in dates.datetime]}

    # Obtain J2000 equatorial coordinates
    with solar_system_ephemeris.set("jpl"):
        for body in bodies:
            coords = get_body(body, dates)
            ra = coords.icrs.ra.deg  # RA in degrees
            dec = coords.icrs.dec.deg  # Dec in degrees

            data[f"{body.capitalize()}_RA"] = ra
            data[f"{body.capitalize()}_Dec"] = dec

    # Create data frame
    df = pd.DataFrame(data)

    # Save data
    if args.filename.endswith(".fits") or args.filename.endswith(".fits.gz"):
        df.to_fits(args.filename, overwrite=True)
    elif args.filename.endswith(".csv"):
        df.to_csv(args.filename, index=False) 
    else:
        raise ValueError("File extension needs to be one of [.fits, .fits.gz .csv]")
    

    print(f"Dades desades a {args.filename}")


if __name__ == "__main__":
    import argparse

    # Default dates (15 years from today)
    end_date_default = datetime.today().strftime('%Y-%m-%d')
    start_date_default = (datetime.today() - timedelta(days=15*365)).strftime('%Y-%m-%d')

    parser = argparse.ArgumentParser(description="Build a catalogue of solar system bodies.")
    parser.add_argument("filename", type=str, help="Output file (fits or csv)")
    parser.add_argument("--start-date", type=str, default=start_date_default, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=end_date_default, help="End date (YYYY-MM-DD)")
    parser.add_argument("--date-step", type=int, default=1, help="Step in days")
    
    args = parser.parse_args()
    main(args)