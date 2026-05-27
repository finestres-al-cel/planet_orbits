import argparse

from planet_orbits.query_horizon import concatenate_queries, OBJIDS    

def main(args):
    
    planets = []
    if args.planet.lower() == "all":
        planets = list(OBJIDS.keys())
    else:
        planet = args.planet.lower()
        if planet not in OBJIDS:
            raise ValueError(f"Invalid target planet. Should be one of {list(OBJIDS.keys())} or 'all'.")
        if planet == "sun":
            planets = [planet]
        else:
            planets = ["sun", planet]

    dfs = []
    for planet in planets:
        print(f"Querying coordinates for {planet}...")
        try:
            df = concatenate_queries(
                args.start_date, args.stop_date, args.step_size, OBJIDS[planet], break_times=args.break_times)
        except RuntimeError as e:
            print(f"Error occurred while querying {planet}: {e}")
            print("Try again with a smaller break_time, or a smaller time range (start_date, stop_date).")
            print("Skipping object.")
            continue
        except Exception as e:
            print(f"An unexpected error occurred while querying {planet}: {e}")
            print("Skipping object.")
            continue
        dfs.append(df)

    if len(dfs) == 0:
        raise RuntimeError("No data was retrived (check logs)")
    if len(dfs) == 1:
        df = dfs[0]
    else:
        print("Merging data into a single dataframe...")
        df = pd.merge(dfs[0], dfs[1], on="Date", how="outer")
        for index in range(2, len(dfs)):
            df = pd.merge(df, dfs[index], on="Date", how="outer")

    # Save data
    if args.filename.endswith(".fits") or args.filename.endswith(".fits.gz"):
        df.to_fits(args.filename, overwrite=True)
    elif args.filename.endswith(".csv"):
        df.to_csv(args.filename, index=False) 
    else:
        raise ValueError("File extension needs to be one of [.fits, .fits.gz, .csv]")
    

    print(f"Dades desades a {args.filename}")


if __name__ == "__main__":

    # Default dates (15 years from today)
    stop_time = '2026-06-20'
    start_time = '1962-01-20'
    step_size = '1h'

    parser = argparse.ArgumentParser(description="Build a catalogue of solar system bodies.")
    parser.add_argument("filename", type=str, help="Output file (fits or csv)")
    parser.add_argument("--start-date", type=str, default=start_time, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--stop-date", type=str, default=stop_time, help="Stop date (YYYY-MM-DD)")
    parser.add_argument(
        "--step-size", type=str, default=step_size, 
        help="Time step. Expected format is 'Xu', where 'X' is an integer and 'u' are the units (d=days, h=hours, m=minutes)")
    parser.add_argument(
        "--break-times", type=str, default="10y", 
        help="Maximum time between start_date and stop_date for each query. Expected format is 'Xu', where 'X' is an integer and 'u' are the units (d=days, m=months, y=years)")
    parser.add_argument(
        "--planet", type=str, default="mars", 
        help=(f"Target planet for the catalogue. Should be one of {list(OBJIDS.keys())}. "
              "To download coordinates for all planets, use 'all'. 'sun' will always be included."))


    args = parser.parse_args()
    main(args)