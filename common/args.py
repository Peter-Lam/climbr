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
        parent_parser = argparse.ArgumentParser(
            add_help=False, formatter_class=custom_formatter)
        parser = argparse.ArgumentParser(
            add_help=False, description='Utility for tracking climbing progress', formatter_class=custom_formatter)
        subparsers = parser.add_subparsers(
            title="Commands", metavar='', dest='command')
        # Options to be inherited by child parsers
        parent_options = parent_parser.add_argument_group('General Options')
        parent_options.add_argument('-h', '--help', action='help',
                                    help='show this help message and exit')
        parent_options.add_argument('-q', '--quiet', action='store_true', dest='silent', help='Quiet mode - suppress system out messages',
                                    required=False)
        parent_options.add_argument('-f', '--force', action='store_true', dest='force',
                                    help='Overwrite any existing files, ElasticSearch, and Kibana settings',
                                    required=False)
        # General Options
        general_option = parser.add_argument_group('General Options')
        general_option.add_argument('-h', '--help', action='help',
                                    help='show this help message and exit')
        general_option.add_argument('--version', action='version',
                                    version='%(prog)s 0.1.0')
        # Init Command
        update_cmd = subparsers.add_parser(
            'init', parents=[parent_parser], add_help=False, help='Initialize and setup climbr visualizations', formatter_class=custom_formatter)
        # Update command
        update_cmd = subparsers.add_parser(
            'update', parents=[parent_parser], add_help=False, help='Update graphs and visualizations with any new climbing logs', formatter_class=custom_formatter)
        # Export Kibana objects
        export_cmd = subparsers.add_parser(
            'export', parents=[parent_parser], add_help=False, help='Export climbing stats and graphs', formatter_class=custom_formatter)
        export_cmd.add_argument('-o',
                                dest='export_name',
                                metavar='filename',
                                help='Change the default export name for Kibana visualizations and objects')
        export_cmd.add_argument('-d', '--dest',
                                dest='export_dest',
                                metavar='destination',
                                help='Change the default destination path for Kibana visualizations and objects')
        # Import Kibana objects, allows for multiple paths - directories and files
        import_cmd = subparsers.add_parser(
            'import', parents=[parent_parser], add_help=False, help='Import existing climbing stats and graphs', formatter_class=custom_formatter)
        import_cmd.add_argument('import_path', nargs='+', metavar='<path>',
                                help='Path to the ndjson object file(s) or directory',)
        # Importing demo files
        demo_cmd = subparsers.add_parser(
            'demo', parents=[parent_parser], add_help=False, help='Use sample data to demo climbr visualizations', formatter_class=custom_formatter)
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
