#!/usr/bin/python3

# --------------------------------
# Quick script to update prexisting bulk JSON data
# --------------------------------

import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
import common.globals as glbs  # noqa
import common.common as common  # noqa


def main():
    file = os.path.join(glbs.ES_BULK_DATA, 'bookings.json')
    bookings = common.load_bulk_json(file)
    temp = 0
    for row in bookings:
        # Make adjustments to row data here
        row['start_minute'] = int(common.str_to_time(row['start_time']).minute)
    common.write_bulk_api(bookings, os.path.join(
        glbs.ES_BULK_DATA, 'bookings.json'), 'bookings')
    print("Update complete")


if __name__ == "__main__":
    main()
