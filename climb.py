#!/usr/bin/python3
'''
The core logic behind tracking climbing sessions and stats
'''
import common.args as cmd_args
import common.validate as validate
import common.common as common
import common.globals as glbs
import os
from common.session import Session


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
    # Would you like to log counter?
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


def get_session_yamls(path):
    '''
    Gather session information from a given directory. If no files are found, will default to using sample_data.
    :param path: path to directory containing session yamls
    :type: str
    :return: list of session files
    :rtype: list of str
    '''
    try:
        if not os.path.exists(path):
            raise Exception(
                f"Unable to find climbing sessions, the path '{path}' does not exist.")
        # Look for logs, if they don't exist, then use the sample data instead
        sessions = common.get_files(
            path, ".*\.yaml$", recursive=False)
        if not sessions:
            print(
                f"Warning: Unable to find logs located at {path}, using sample data instead...")
            sessions = common.get_files(
                glbs.SAMPLE_DATA_DIR, ".*\.yaml$", recursive=False)
            if not sessions:
                raise Exception("Unable to locate sample data.")
        return sessions
    except Exception as ex:
        raise ex


def main():
    try:
        args = cmd_args.init()
        cmd = args.command
        # Variables
        output_dir = validate.directory(glbs.OUTPUT_DIR)
        if cmd == 'log':
            raise Exception("This command is currently not supported")
            sessions = []
            # Creating Session
            for path in args.log_path:
                log = common.load_yaml(path)
                # session.append(Session(log))
                validate.climbing_log(log)
            # create_record()
            # common.write_bulk_api(updated_values, )
            # common.update_bulk_json()
        elif cmd == 'update':
            logs_found = False
            session_logs = get_session_yamls(glbs.INPUT_DIR)
            # Loop through all climbing logs, normalize and add additional information
            session_data = []
            project_data = []
            counter_data = []
            for log in session_logs:
                climbing_session = Session(log)
                session_data.append(climbing_session.toDict())
                counter_data.extend(climbing_session.getCounters())
                project_data.extend(climbing_session.getProjects())
            common.write_bulk_api(session_data, os.path.join(
                output_dir, "sessions.json"), 'sessions')
            common.write_bulk_api(counter_data,  os.path.join(
                output_dir, "counters.json"), 'counters')
            common.write_bulk_api(project_data,  os.path.join(
                output_dir, "projects.json"), 'projects')
            print(
                f"Climbing information successfully updated! \nPlease use 'climb.py show' to view statistics and graphs")

        elif cmd == 'show':
            # Gathering mapping information for bookings and session
            # Preparing Elasticsearch and Kibana for data consumption
            for index in glbs.ES_INDEX_NAME:
                common.create_index(glbs.ES_URL, index, validate.file(
                    os.path.join(glbs.ES_DIR, f"{index}_mapping.json")))
                common.create_index_pattern(glbs.KIBANA_URL, index)
            # Importing all data into elasticSearch
            common.upload_to_es(glbs.ES_URL, output_dir)
            print(f"Visualizations and stats are ready at {glbs.KIBANA_URL}")
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    try:
        main()
    # except KeyboardInterrupt:
    #     # TODO
    #     # rollback()
    #     raise
    except Exception as ex:
        # print(ex)
        raise ex
