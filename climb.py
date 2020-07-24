#!/usr/bin/python
'''
The core logic behind tracking climbing sessions and stats
'''
import common.args as cmd_args
import common.file_util as file
import common.validate as validate
import pprint  # TODO: Remove this


def get_user_input():
    '''
    Ask the user for information about the climbing session
    :param list_values: the list of ioc dictionaries to update
    :type list_values: list of dict
    :return clean_list: returns cleaned information
    :return duplicate_count: returns number of duplicated detected
    :rtype clean_list: list of dict
    :rtype duplicate_count: int
    '''
    print("Hello world")
    # *Location?
    # *Style of climbing [indoor bouldering, outdoor bouldering, indoor lead, outdoor lead, autobelay]
    # Description : Null if left empty
    # *Date: YYYY-MM-DD
    # Time start& end HH:MM AM/PM
    # Climbers
    # injury? Y/N if yes then describe
    # Would you like to log session_counter?
    #   grade? [V-Scale, Font, Comp, ungraded]
    #   Number of flashes/ redpoint / repeat / attempts
    #   Log another?
    #   Or just loop increments with skip option
    # Would you like to log a specific climb?
    #   name: Describe the problem or give it a name
    #   location: [slab / left overhang / comp wall / cave / right overhang / slabish]
    #   style: [dynamic, crimp, compression, overhang, competition, coordination, other]
    #   if other, what style?
    #   grade: [V-Scale, Font, Comp, ungraded]
    #   Any notes about this climb?
    # media - add url and validate, loop

    # Return object with session information


def main():
    args = cmd_args.init()
    cmd = args.command
    if cmd == 'log':
        for path in args.log_path:
            log = file.load_yaml(path)
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(log)
            validate.climbing_log(log)
            print("G")
    elif cmd == 'update':
        raise Exception("TODO: Currently not implemented")
    elif cmd == 'show':
        raise Exception("TODO: Currently not implemented")
    else:
        raise Exception(f"Unknown command:{cmd}")

    # if config file, validate that the correct information is present
    # read config into object
    # validator.is_date()
    # validator.is_number() - attempts are above 0 and integers
    # TODO: If a grade is not listed in "Session Counter" then assume 0
    # TODO: call function to add geo-location based on session info
    # TODO: calculate duration of climbing

    # If no cofig, get user information
    session_info = get_user_input()

    # Verify with user about information
    # Option to modify if needed
    # If not from config, Write to YAML to have a papertail for logs with format YYYY-MM-DD
    # If config, edit the file and make the changes
    # validator.file_exists()

    # Logging information...
    # Update elasticsearch and kibana
    # YAML* -> BULK_JSON-> Elastic Search -> Kibana
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # TODO
        # rollback()
        raise
    except Exception as ex:
        raise ex
