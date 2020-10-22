#!/usr/bin/python3
'''
The core logic behind tracking climbing sessions and stats
'''
from datetime import datetime
import common.args as cmd_args
import common.validate as validate
import common.common as common
import common.globals as glbs
import os
import requests
import urllib3
from time import sleep
from common.session import Session
from operator import add


def get_session_yamls(path):
    '''
    Gather session information from a given directory.
    :param path: path to directory containing session yamls
    :type: str
    :return: list of session files
    :rtype: list of str
    '''
    try:
        if not os.path.exists(path):
            raise Exception(
                f"Unable to find climbing sessions, the path '{path}' does not exist.")
        sessions = common.get_files(
            path, ".*\.yaml$", recursive=False)
        if not sessions:
            raise Exception(
                "Unable to find logs located at {path}. Consider using the 'demo' command to view sample data...")
        return sessions
    except Exception as ex:
        raise ex


def main():
    try:
        args = cmd_args.init()
        cmd = args.command
        # Variables
        data_dir = validate.directory(glbs.ES_BULK_DATA)
        es_url = glbs.ES_URL if 'DOCKER' not in os.environ else glbs.ES_URL_DOCKER
        kibana_url = glbs.KIBANA_URL if 'DOCKER' not in os.environ else glbs.KIBANA_URL_DOCKER
        # Command-line Options
        # Initializing Kibana and ES with mappings and visualizations
        if cmd == 'init':
            # Need to wait for Kibana and ES to start up whilst using docker
            # Choosing to write this here instead of bash script + docker-compose for maintainability
            if 'DOCKER' in os.environ:
                waiting = True
                timeout_counter = 0
                # Wait to establish connection, and timeout if it takes too long
                while waiting:
                    try:
                        response = requests.get(kibana_url).status_code
                    # Catching error if ES/Kibana isn't ready yet
                    except Exception:
                        response = 400
                        pass
                    if response == 200:
                        waiting = False
                    else:
                        if timeout_counter >= 5:
                            raise Exception(
                                f"Unable to ping Kibana instance located at '{kibana_url}'")
                        print(
                            f"ElasticSearch and Kibana services are not ready yet, trying again in 60 seconds")
                        sleep(60)
                        timeout_counter += 1

            # Preparing Elasticsearch and Kibana for data consumption
            for index in glbs.ES_INDEX_NAME:
                common.create_index(es_url, index, validate.file(
                    os.path.join(glbs.ES_MAPPINGS, f"{index}_mapping.json")), silent=args.silent, force=args.force)
                common.create_index_pattern(
                    kibana_url, index, silent=args.silent, force=args.force)
            # Importing visualizations
            common.import_kibana(
                kibana_url, ndjson=common.get_files(glbs.ES_DIR, "visualizations.ndjson").pop(), silent=args.silent)
        # Uploading user data into ES
        if cmd == 'update' or cmd == 'demo':
            # Loop through all climbing logs, normalize and add additional information
            if not args.silent:
                print("[1/5] Retreiving climbing logs...")
            if cmd == 'demo':
                session_logs = get_session_yamls(glbs.SAMPLE_DATA_DIR)
            else:
                session_logs = get_session_yamls(glbs.INPUT_DIR)
            sessions = []
            session_data = []
            project_data = []
            counter_data = []
            project_list = {}
            if not args.silent:
                print("[2/5] Enhancing and normalizing data...")
            for log in session_logs:
                try:
                    # Creating Session class from logs
                    climbing_session = Session(log)
                    # Create and maintain a running list of projects and a total counter across all Sessions
                    if climbing_session.Projects:
                        for project in climbing_session.Projects:
                            if project.name in project_list.keys():
                                updated_total = [
                                    x + y for x, y in zip(project_list[project.name].get_counters(), project.get_counters())]
                                # Remove is_last from the previous project instance and assign the new value to the current project
                                project_list[project.name].set_is_last(False)
                                project.set_is_last(True)
                                # Increase the running counters and update the project with the current running counter
                                project.set_total_counter(
                                    updated_total[0], updated_total[1], updated_total[3], updated_total[4], updated_total[5], updated_total[6])
                                # del project_list[project.name]
                                project_list[project.name] = project
                            # If the project isn't in the running list, add it.
                            # Total counter is default the same as counter, so don't change the values
                            else:
                                project.set_is_last(True)
                                project_list[project.name] = project
                    sessions.append(climbing_session)

                except Exception as ex:
                    raise Exception(f"Unable to update '{log}'. {ex}")
            # Loop through the list of Sessions and update the output lists
            for session in sessions:
                session_data.append(session.toDict())
                counter_data.extend(session.getCounters())
                project_data.extend(session.getProjects())
            if not args.silent:
                print("[3/5] Writing climbing data to json...")
            common.write_bulk_api(session_data, os.path.join(
                data_dir, "sessions.json" if cmd == 'update' else "sessions_demo.json"), 'sessions')
            common.write_bulk_api(counter_data,  os.path.join(
                data_dir, "counters.json" if cmd == 'update' else "counters_demo.json"), 'counters')
            common.write_bulk_api(project_data,  os.path.join(
                data_dir, "projects.json" if cmd == 'update' else "projects_demo.json"), 'projects')
            # Importing all data into elasticSearch
            if not args.silent:
                print("[4/5] Uploading data into ElasticSearch...")
            common.upload_to_es(es_url, data_dir, silent=True)
            if not args.silent:
                print(
                    f"[5/5] Visualizations and stats are ready at {kibana_url}/app/dashboard")
        # Exporting Kibana and ES Objects
        elif cmd == 'export':
            # Default export name used (ex. climbr_2020-09-19_02-55-15) unless overwritten by -o option
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = args.export_name if args.export_name else f"climbr_{timestamp}"
            # Default export location used (output directory) unless overwritten but -d/--dest option
            destination = os.path.join(args.export_dest, filename) if args.export_dest else os.path.join(
                glbs.OUTPUT_DIR, f"{filename}.ndjson")
            common.export_kibana(kibana_url, destination, silent=args.silent)
        # Import Kibana and ES Objects from a ndjson file
        elif cmd == 'import':
            for path in args.import_path:
                if os.path.isfile(path):
                    if '.ndjson' in os.path.splitext(path)[1]:
                        common.import_kibana(
                            kibana_url, path, silent=args.silent)
                    else:
                        raise TypeError(
                            f"Unable to import '{path}'. Invlaid file extension, must be '.ndjson'.")
                # If the given path is a directory, then gather all .ndjson files
                elif os.path.isdir(path):
                    files = common.get_files(path, ".*\.ndjson$")
                    for file in files:
                        common.import_kibana(
                            kibana_url, file, silent=args.silent)
                else:
                    raise Exception(
                        f"Unable to import '{path}'. File path or directory does not exist.")
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
