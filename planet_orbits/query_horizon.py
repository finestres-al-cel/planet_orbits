from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import pandas as pd
import requests

OBJIDS = {
    "sun": 10,
    "mercury": 199,
    "venus": 299,
    #"earth": 399,
    "mars": 499,
    "jupiter": 599,
    "saturn": 699,
    "uranus": 799,
    "neptune": 899,
}

def concatenate_queries(start_time, stop_time, step_size, objid, break_times="10y"):
    """
    Recursively query the Horizon system for ephemerides.

    Call the function query with smaller date windows to avoid queries that are too large.
    Concatenate the results of the different sub-queries.

    Arguments
    ---------
    start_time: str
    Starting time. Expected format is 'yyyy-mm-dd'

    stop_time: str
    Stopping time. Expected format is 'yyyy-mm-dd'

    step_size: str
    Time step. Expected format is 'Xu', where 'X' is an integer and 'u' are the units (d=days, h=hours, m=minutes)
    See https://ssd-api.jpl.nasa.gov/doc/horizons.html#stepping for details
    Examples:
        '1d' gets one row every day
        '12h' gets one row every 12 hours

    objid: int
    ID of the queried body. Common object IDs:
        Sun: 10
        Mercury: 199
        Venus: 299
        Earth: 399
        Mars: 499
        Jupiter: 599
        Saturn: 699
        Uranus: 799
        Neptune: 899

    break_times: str, Default: '10y'
    Maximum time between start_date and stop_date. 
    Expected format is 'Xu', where 'X' is an integer and 'u' are the units (d=days, m=months, y=years)
    The last interval might be shorter
    Examples:
        '10y': The time between start_date and stop_date is 10 years
        '2m': The time between start_date and stop_date is 2 months
        
    Return
    ------
    df: pd.DataFrame
    A dataframe with the requested coordinates    
    """
    # convert dates
    start_date = datetime.strptime(start_time, "%Y-%m-%d").date()
    stop_date = datetime.strptime(stop_time, "%Y-%m-%d").date()

    # Parse the break_time (e.g., '15d', '2m', '1y')
    amount = int(break_times[:-1])
    unit = break_times[-1].lower()
    if unit == "d":
        delta = relativedelta(days=amount)
    elif unit == "m":
        delta = relativedelta(months=amount)
    elif unit == "y":
        delta = relativedelta(years=amount)
    else:
        raise ValueError(
            "Invalid unit in break_time. Use 'd' for days, 'm' for months, or 'y' for years."
        )

    # Loop and query the chunks
    dfs = []
    current_start = start_date
    while current_start < stop_date:
        # Calculate the potential end of the current chunk
        current_stop = current_start + delta
        
        # Ensure we don't overshoot the final end_date
        if current_stop > stop_date:
            current_stop = stop_date

        # Query the chunks
        current_start_time = current_start.strftime("%Y-%m-%d")
        current_stop_time = current_stop.strftime("%Y-%m-%d")
        print(f"Running query with start_time={current_start_time}, stop_time={current_stop_time}, step_size={step_size}")
        df = query(current_start_time, current_stop_time, step_size, objid)
    
        
        dfs.append(df)
        
        # Move the next start date to the day after the current end
        #current_start = current_end + relativedelta(days=1)
        current_start = current_stop

    full_df = pd.concat(dfs)
    full_df = full_df.drop_duplicates().reset_index(drop=True)
    return full_df

def parse_query_results(results):
    header = True
    date_list = []
    ra_list = []
    dec_list = []
    body = None
    
    lines = results.split("\n")
    for line in lines:
        if line.startswith("$$EOE"):
            break
        if header and line.startswith(" Revised:"):
            body = line.split()[4]
        if header and line.startswith("Projected output length"):
            raise RuntimeError(f"Query problem: {line}")
        if not header:
            cols = line.split()
            date_list.append(f"{cols[0]} {cols[1]}")
            ra_list.append(float(cols[2]))
            dec_list.append(float(cols[3]))
        if line.startswith("$$SOE"):
            header = False
    df = pd.DataFrame({
        "date": date_list,
        f"{body.lower()}_ra": ra_list,
        f"{body.lower()}_dec": dec_list,
    })
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def query(start_time, stop_time, step_size, objid):
    """
    Query the Horizon system for ephemerides.

    Call the function parse_query_results to format the results to a pandas DataFrame

    Arguments
    ---------
    start_time: str
    Starting time. Expected format is 'yyyy-mm-dd'

    stop_time: str
    Stopping time. Expected format is 'yyyy-mm-dd'

    step_size: str
    Time step. Expected format is 'Xu', where 'X' is an integer and 'u' are the units (d=days, h=hours, m=minutes)
    See https://ssd-api.jpl.nasa.gov/doc/horizons.html#stepping for details
    Examples:
        '1d' gets one row every day
        '12h' gets one row every 12 hours

    objid: int
    ID of the queried body. Common object IDs:
        Sun: 10
        Mercury: 199
        Venus: 299
        Earth: 399
        Mars: 499
        Jupiter: 599
        Saturn: 699
        Uranus: 799
        Neptune: 899

    Return
    ------
    df: pd.DataFrame
    A dataframe with the requested coordinates    
    """
    # Define API URL and SPK filename:
    base_url = 'https://ssd.jpl.nasa.gov/api/horizons.api'
    spk_filename = 'spk_file.bsp'
        
    # Build the appropriate URL for this API request:
    # IMPORTANT: You must encode the "=" as "%3D" and the ";" as "%3B" in the
    #            Horizons COMMAND parameter specification.
    url = base_url
    url += "?format=json&EPHEM_TYPE=OBSERVER&OBJ_DATA=YES"
    url += f"&COMMAND='{objid}'&START_TIME='{start_time}'&STOP_TIME='{stop_time}'&STEP_SIZE='{step_size}'"
    url += "&ANG_FORMAT='DEG'&QUANTITIES='1,18'"
    
    # Submit the API request and decode the JSON-response:
    response = requests.get(url)
    data = json.loads(response.text)

    # parse results
    df = parse_query_results(data.get("result"))
        
    return df
