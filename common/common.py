#!/usr/bin/python3
'''
This module contains common used functions by scripts within Climbing-Tracker
'''

import os
import json
import sys
import yaml

def convert_grades(grade):
    # TODO: Convert climbing grades to normalize data
    # https://www.mec.ca/en/explore/climbing-grade-conversion
    raise Exception("TODO")


def load_json(path):
    '''
    Opens and loads a JSON file
    :param path: Path to JSON
    :type path: str
    :raises Exception: JSON path does not exist
    :return: File contents
    :rtype: json
    '''
    if os.path.exists(path):
        raise Exception(f"The path: {path} does not exist")
    with open(path, 'r') as file:
        return json.load(file)


def load_yaml(path):
    '''
    Reads the configuration file and returns the object
    :param path: Path to yaml
    :type path: str
    :raises Exception: Yaml path does not exist
    :return: Config contents
    :rtype: yaml
    '''
    try:
        if not os.path.exists(path):
            raise Exception(f"The path: {path} does not exist")
        with open(path, 'r') as stream:
            return yaml.safe_load(stream)
    except Exception as ex:
        raise Exception(f"Unable to read climbing log, formatting error found {ex.args[3]}")

def write_log(log, output_path):
    '''
    Writing to log file
    :type output_path: str
    '''
    try:
        if os.path.isfile(output_path):
            with open(output_path, "a") as file:
                file.write(log + '\n')
        else:
            with open(output_path, 'w') as file:
                file.write(log + '\n')
    except Exception as ex:
        raise ex


def write_json(data, output_path):
    '''
    Reads values and writes into output file path,
    will overwrite file if already exists
    :param data: Ioc data to add write to json
    :param output_path: Output path including filename.json
    :type data: list of dict
    :type output_path: str
    '''

    try:
        if os.path.isfile(output_path):
            with open(output_path, "a") as file:
                json.dump(data, file, indent=4)
        else:
            with open(output_path, 'w') as file:
                json.dump(data, file, indent=4)
    except Exception as ex:
        raise ex

def write_bulk_api(data, output_path, index_name):
    '''
    Writes to a json file in bulk api format given a list of information,
    if the output path already exists, will overwrite
    :param data: ioc data to add write to json
    :param output_path: the path to the json in bulk api format
    :param index_name: Index name for elasticsearch
    :type data: list of dict
    :type output_path: str
    '''
    try:
        new_contents = []
        current_index = 0
        # If the data is a dict, then assume it's one object
        if type(data) is dict:
            new_contents.append(json.dumps(
                    {"index": {"_index": index_name, "_id": current_index}}))
            new_contents.append(json.dumps(data))
        # If it's a list then, then assume it's multiple
        elif type(data) is list:
            for row in data:
                new_contents.append(json.dumps(
                    {"index": {"_index": index_name, "_id": current_index}}))
                current_index += 1
                new_contents.append(json.dumps(row))
        else:
            raise Exception(f"Object type '{type(data)} is not supported. Must be list or dict")
        
        with open(output_path, "w") as file:
            for line in new_contents:
                file.write(line + "\n")
    except Exception as ex:
        raise ex

def get_last_index(bulk_api_path):
    '''
    Retreiving the last index from a JSON in bulk api format,
    will raise exception if file path doesn't exist
    :param bulk_api_path: File path to json in bulk api format
    :type bulk_api_path: str
    :raises Exception: Bulk API path does not exist
    :return last_index: The last index in the json
    :rtype last_index: int
    '''
    if not os.path.exists(bulk_api_path):
        raise Exception(f"The path: {bulk_api_path} does not exist")

    with open(bulk_api_path) as file:
        lines = file.read().splitlines()
        last_index = (json.loads(lines[-2]))["index"]["_id"]
        return last_index


def update_bulk_api(data, output_path, index_name):
    '''
    Updating an existing json in bulk api format with new ioc information,
    will raise exception if file path doesn't exist
    :param data: Ioc information that is to be added to the json
    :param output_path: The path to the json in bulk api format
    :param index_name: Index name for elasticsearch
    :raises Exception: Output path does not exist
    :type data: list of dict
    :type output_path: str
    '''
    try:
        # Create a new file if it doesn't exist
        if not os.path.exists(output_path):
            print(f"'{output_path}' not found, creating file and writing...")
            write_bulk_api(data, output_path, index_name)
        elif data:
            updated_list = []
            current_index = get_last_index(output_path) + 1

            # If the data is a dict, then assume it's one object
            if type(data) is dict:
                updated_list.append(json.dumps(
                        {"index": {"_index": index_name, "_id": current_index}}))
                updated_list.append(json.dumps(data))
                current_index += 1
            # If it's a list then, then assume it's multiple
            elif type(data) is list:
                for value in data:
                    updated_list.append(json.dumps(
                        {"index": {"_index": index_name, "_id": current_index}}))
                    updated_list.append(json.dumps(value))
                    current_index += 1
            else:
                raise Exception(f"Object type '{type(data)} is not supported. Must be list or dict")
            # Write to the JSON file
            with open(output_path, "a") as file:
                for line in updated_list:
                    file.write(line + "\n")
    except Exception as ex:
        raise ex


def delete_file(path):
    '''
    Deletes file if it exists
    :param path: Path of file
    :type: str
    '''
    if os.path.exists(path):
        os.remove(path)
