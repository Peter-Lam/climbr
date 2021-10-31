#!/usr/bin/python3

"""Quick script to update prexisting bulk JSON data."""

import os
import sys
from datetime import datetime  # noqa

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
import common.common as common  # noqa
import common.globals as glbs  # noqa


def get_bookings():
    """Retreive booking data and return the data."""
    file = os.path.join(glbs.ES_BULK_DATA, "bookings.json")
    return common.load_bulk_json(file)


def update():
    """Update the existing json file."""
    # Get data
    bookings = get_bookings()
    for row in bookings:
        # Set dataframe depending on the location of the booking
        if "percent_full" not in row.keys():
            row["percent_full"] = (row["reserved_spots"] / row["capacity"]) * 100
    common.write_bulk_api(
        bookings, os.path.join(glbs.ES_BULK_DATA, "bookings.json"), "bookings"
    )
    print("Update complete")


def main():
    """Retroactively update data."""
    update()


if __name__ == "__main__":
    main()
