#!/usr/bin/python
'''
Parsing arguments for climb.py
'''
import argparse
import sys
import os


def init():
    '''
    Initializing argparser for climb.py
    '''
    try:
        # Parsers
        def custom_formatter(prog): return argparse.RawTextHelpFormatter(
            prog, max_help_position=50)
        parser = argparse.ArgumentParser(
            add_help=True, description='Utility for gathering booking data from climbing gyms', formatter_class=custom_formatter)
        general_option = parser.add_argument_group('General Options')
        general_option.add_argument('--version', action='version',
                                    version='%(prog)s 1.2.0')
        parser.add_argument('-l', nargs='+',
                            dest='locations',
                            metavar='location(s)',
                            required=True,
                            help=f'Climbing Gym locations [Altitude_Kanata, Altitude_Gatineau, Coyote_Rock_Gym]')
        parsed = parser.parse_args()
        # Checking for choices after parsing because '\r' is present in cronjobs
        choices = ['Altitude_Kanata', 'Altitude_Gatineau', 'Coyote_Rock_Gym']
        if '\r' in parsed.locations:
            parsed.locations.remove('\r')
        for location in parsed.locations:
            if location not in choices:
                print(
                    f"bookings.py: error: argument -l: invalid choice: '{location}'. Must be one or more of the following: {choices}")
                sys.exit()
        return parsed
    except Exception as ex:
        str(sys.argv)
        raise ex
