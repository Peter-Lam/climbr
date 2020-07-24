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
        parent_parser = argparse.ArgumentParser(add_help=False)
        parser = argparse.ArgumentParser(
            add_help=False, description='Utility for tracking climbing progress')
        subparsers = parser.add_subparsers(
            title="Commands", metavar='', dest='command')

        # Options to be inherited by child parsers
        parent_options = parent_parser.add_argument_group('General Options')
        parent_options.add_argument('-h', '--help', action='help',
                                    help='show this help message and exit')
        parent_options.add_argument('-f', '--force', action='store_true', dest='force',
                                    help='Overwrite any existing files',
                                    required=False)
        # General Options
        general_option = parser.add_argument_group('General Options')
        general_option.add_argument('-h', '--help', action='help',
                                    help='show this help message and exit')
        general_option.add_argument('--version', action='version',
                                    version='%(prog)s 0.1.0')

        # Log command
        log_cmd = subparsers.add_parser(
            'log', parents=[parent_parser], add_help=False, help='Log a new climbing session')
        log_cmd.add_argument('log_path', nargs='+', metavar='<path>',
                             help='Path to the log file(s)',)
        # Update command
        update_cmd = subparsers.add_parser(
            'update', parents=[parent_parser], add_help=False, help='Update graphs and visualizations with any new climbing logs')

        # Show command
        show_cmd = subparsers.add_parser(
            'show', add_help=False, help='Show climbing stats and graphs')

        args = parser.parse_args()
        # If "py climb.py" called without subparser, then just display help
        if (args.command == None):
            parser.print_help(sys.stderr)
            sys.exit(0)
        # Checking validity of paths when using 'log' command
        if args.command == 'log':
            for path in args.log_path:
                if not os.path.isfile(path):
                    parser.error(
                        f"Unable to log climbing entry, the file '{path}' does not exist!")
        return args
    except Exception as ex:
        raise ex
