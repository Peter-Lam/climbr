#!/usr/bin/python
"""Parsing arguments for climb.py."""

import argparse
import sys


def init():
    """Parse command args for climb.py."""
    try:
        # Parsers
        def custom_formatter(prog):
            return argparse.RawTextHelpFormatter(prog, max_help_position=50)

        parser = argparse.ArgumentParser(
            add_help=True,
            description="Utility for gathering booking data from climbing gyms",
            formatter_class=custom_formatter,
        )
        general_option = parser.add_argument_group("General Options")
        general_option.add_argument(
            "--version", action="version", version="%(prog)s 3.4.0"
        )
        parser.add_argument(
            "-l",
            nargs="+",
            dest="locations",
            metavar="location(s)",
            required=True,
            help="Climbing Gym locations [Altitude_Gatineau, "
            "Altitude_Kanata, Coyote_Rock_Gym]",
        )
        parsed = parser.parse_args()
        # Checking for choices after parsing because '\r' is present in cronjobs
        choices = ["Altitude_Gatineau", "Altitude_Kanata", "Coyote_Rock_Gym"]
        if "\r" in parsed.locations:
            parsed.locations.remove("\r")
        for location in parsed.locations:
            if location not in choices:
                print(
                    f"bookings.py: error: argument -l: invalid choice: '{location}'."
                    f" Must be one or more of the following: {choices}."
                )
                sys.exit()
        return parsed
    except Exception as ex:
        str(sys.argv)
        raise ex
