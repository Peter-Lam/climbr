#!/usr/bin/python3
'''
The core logic behind tracking climbing sessions and stats
'''
import common.args as cmd_args
import common.validate as validate
import common.common as common
import common.globals as glbs
import urllib
import os
import requests
from elasticsearch import Elasticsearch
from common.session import Session


def connect_to_es(es_url):
    '''
    Try to connect to Elasticsearch and return ES object, raises exception if unable to ping
    :param es_url: url to the Elasticsearch instance
    :type: str
    :return: ES Instance
    :rtype: obj
    :raises Exception: Elasticsearch is not running
    '''
    try:
        es = Elasticsearch([es_url], verify_certs=True)
        if not es.ping():
            raise Exception(
                "Unable to ping Elasticsearch, please confirm connection and try again.")
        return es
    except Exception as ex:
        raise ex
    # TODO: Check for docker, and if installed, build ELK stack images


def create_index(es_url, index_name, mapping_path):
    '''
    Create an Elasticsearch index (table) using a mapping to define field types
    :param es_url: url to Elasticsearch instance
    :param index_name: Name of index
    :param mapping_path: Path to a json
    :type es_url: str
    :type index_name: str
    :type mapping_path: str
    :raises Exception: path is not a directory, does not exist or Elasticsearch is not running
    '''
    try:
        # Connecting to Elasticsearch
        es = connect_to_es(es_url)
        # Deleting any old indexes
        if es.indices.exists(index_name):
            es.indices.delete(index_name)
        # TODO: If it exists, then do nothing, else create index
        mapping = common.load_file(mapping_path)
        try:
            print(f"Creating {index_name} index...")
            es.indices.create(index_name, body=mapping)
            print(f"Successfully created {index_name} index!")
        except Exception as ex:
            raise Exception(
                f"Unable to create mapping from '{mapping_path}'")
    except Exception as ex:
        raise ex


def create_index_pattern(kibana_url, index_name):
    '''
    Create a general Kibana index pattern by calling a cURL command
    :param kibana_url: url to the Kibana instance
    :param index_name: Name of index
    :type index_name: str
    :type mapping_path: str
    :raises Exception: path is not a directory, does not exist
    '''
    try:
        # Try to ping Kibana
        if requests.get(kibana_url).status_code != 200:
            raise Exception(
                f"Unable to ping Kibana instance located at '{kibana_url}'")
        index_url = urllib.parse.urljoin(
            kibana_url, f"api/saved_objects/index-pattern/{index_name}")
        # Create index pattern if not present
        if requests.get(index_url).status_code != 200:
            headers = {'kbn-xsrf': 'true',
                       'Content-Type': 'application/json'}
            data = '{{ "attributes": {{ "title": "{}*" }} }}'.format(
                index_name)
            print(f"Creating index pattern for {index_name}...")
            response = requests.post(
                index_url, headers=headers, data=data)
            if response.status_code == 200:
                print(f"Successfully created index pattern for {index_name}!")
            else:
                # TODO: Log respons output on error
                # response.json()
                raise Exception(
                    f"{response} Unable to create bookings index pattern")
        else:
            print(
                f"Found existing index pattern for {index_name}, skipping creation")
    except Exception as ex:
        raise ex


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


def import_data(es_url, path, recursive=False):
    '''
    Importing bulk json files into Elasticsearch
    :param es_url: url to Elasticsearch instance
    :param path: path to directory to import
    :param recursive: optional bool to collect files from sub-dirs
    :type es_url: str
    :type path: str
    :type recursive: bool
    :raises Exception: path is not a directory, does not exist
    '''
    try:
        # Connecting to Elasticsearch
        es = connect_to_es(es_url)
        # Load all json files located in output dir into ES
        bulk_json = common.get_files(path, ".*\.json$")
        if not bulk_json:
            raise Exception(
                f"Unable to find files to upload, please use 'climb.py update' first then re-run 'climb.py show'")
        for file in bulk_json:
            content = common.load_file(file)
            es_response = es.bulk(content)
            # If there are errors, look for problematic index and alert user
            if es_response['errors']:
                es_error = ''
                for item in es_response['items']:
                    if item['index']['status'] != 200:
                        id = item['index']['_id']
                        exception_type = item['index']['error']['type']
                        reason = item['index']['error']['reason']
                        es_error += f"  [id:{id}] {exception_type}: {reason} \n"
                # print(es_response)
                raise Exception(
                    f"Unable to upload '{file}' into Elasticsearch do to the following rows:\n{es_error}")
            else:
                print(f"'{file}' has been successfully uploaded!")
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
            session_file = os.path.join(output_dir, "sessions.json")
            session_logs = get_session_yamls(glbs.INPUT_DIR)
            # Loop through all climbing logs, normalize and add additional information
            final_data = []
            for log in session_logs:
                climbing_session = Session(log)
                final_data.append(climbing_session.toDict())
            common.write_bulk_api(final_data, session_file, 'sessions')
            print(
                f"Climbing information successfully updated at '{session_file}'!\nPlease use 'climb.py show' to view statistics and graphs")

        elif cmd == 'show':
            # Gathering mapping information for bookings and session
            bookings_mapping = validate.file(
                os.path.join(glbs.ES_DIR, 'bookings_mapping.json'))
            session_mapping = validate.file(
                os.path.join(glbs.ES_DIR, 'session_mapping.json'))

            # Preparing Elasticsearch and Kibana for data consumption
            create_index(glbs.ES_URL, 'bookings', bookings_mapping)
            create_index_pattern(glbs.KIBANA_URL, 'bookings')
            create_index(glbs.ES_URL, 'sessions', session_mapping)
            create_index_pattern(glbs.KIBANA_URL, 'sessions')

            # Importing sessions and booking formation into elasticSearch
            import_data(glbs.ES_URL, output_dir)
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
