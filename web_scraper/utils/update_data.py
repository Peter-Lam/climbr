#!/usr/bin/python3

# --------------------------------
# Quick script to update prexisting bulk JSON data
# --------------------------------

import os
import sys
from datetime import datetime

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
import common.common as common  # noqa
import common.globals as glbs  # noqa


def get_bookings():
    """
    Retreive booking data and return the data
    """
    file = os.path.join(glbs.ES_BULK_DATA, "bookings.json")
    return common.load_bulk_json(file)


def update():
    """
    Edit this function to update the existing json file
    """
    # # Get data
    # bookings = get_bookings()
    # for row in bookings:
    #     # Set dataframe depending on the location of the booking
    #     df = ott if row['location'] in [
    #         'Altitude Kanata', 'Coyote Rock Gym'] else gat
    #     # reformat the date from json
    #     date = datetime.fromisoformat(
    #         row['retrieved_at']).strftime(("%Y-%m-%d"))
    #     # Look for booking data with weather, if it doesn't match then ignore
    #     weather = df.loc[df['date'] == date]
    #     if weather.shape[0] >= 1:
    #         for col in list(weather):
    #             if weather.shape[0] > 1:
    #                 print("Warning: More than one value found for weather, using last")
    #                 row[col] = weather.iloc[-1][col]
    #             else:
    #                 row[col] = weather.iloc[0][col]
    #     else:
    #         print(f"No weather data found for {date}")
    #         pass
    # common.write_bulk_api(bookings, os.path.join(
    #     glbs.ES_BULK_DATA, 'bookings22.json'), 'bookings')
    # print("Update complete")


def main():
    update()


if __name__ == "__main__":
    main()
