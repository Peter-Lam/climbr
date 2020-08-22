#!/usr/bin/python3
'''
This module contains common used functions by scripts within Climbing-Tracker
'''
import json
import os
import re
import sys
import yaml
import common.validate as validate
from datetime import datetime


def convert_grades(grade):
    # TODO: Convert climbing grades to normalize data
    # https://www.mec.ca/en/explore/climbing-grade-conversion
    raise Exception("TODO")


def convert_to_hhmm(time):
    '''
    Coverting time string to HH:MM AM/PM format, throwing an error if unexpected format
    :param time: time in 12 hour format
    :type time: str
    :raises Exception: Unexpected time format
    :return: Time in HH:MM AM/PM format
    :rtype: str
    '''
    try:
        # Declaring regex pattens
        hh_mm = re.compile("^(1[0-2]|0[1-9]):[0-5][0-9] (AM|PM)$")
        h_mm = re.compile("^([1-9]):[0-5][0-9] (AM|PM)$")
        hh = re.compile("^(1[0-2]|0[1-9]) (AM|PM)$")
        h = re.compile("^[1-9] (AM|PM)$")
        if hh_mm.match(time) or h_mm.match(time):
            return datetime.strftime(datetime.strptime(time, "%I:%M %p"), "%I:%M %p")
        elif hh.match(time) or h.match(time):
            return datetime.strftime(datetime.strptime(time, "%I %p"), "%I:%M %p")
        # TODO: Convert 24 hour format to 12 hour
        else:
            raise Exception(
                f"Unexpected format. Unable to convert '{time}'to HH:MM AM/PM format.")
    except Exception as ex:
        raise ex


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
        raise Exception(
            f"Unable to read climbing log, formatting error found {ex.args[3]}")


def load_file(path):
    '''
    Reads the contents of a file and returns a string with contents
    :param path: Path to file
    :type path: str
    :raises Exception: file path does not exist
    :return: file contents
    :rtype: str
    '''
    try:
        if not os.path.exists(path):
            raise Exception(f"The path: {path} does not exist")
        with open(path, 'r') as file:
            return file.read()
    except Exception as ex:
        raise Exception(f"Unable to read file: {path}")


def write_log(log, output_path):
    '''
    Writing to log file, will create file and parent folder if the path doesn't exist
    :param log: Log information
    :param output_path: path to log file
    :type log: str
    :type output_path: str
    '''
    try:
        if not os.path.exists(os.path.dirname(output_path)):
            print(f"'os.path.dirname(output_path)' does not exist, creating folder")
            os.makedirs(os.path.dirname(output_path))
        file_perm = 'a' if os.path.isfile(output_path) else 'w'
        with open(output_path, file_perm) as file:
            file.write(log + '\n')
    except Exception as ex:
        raise ex


def write_json(data, output_path):
    '''
    Reads values and writes into output file path,
    :param data: Ioc data to add write to json
    :param output_path: Output path including filename.json
    :type data: list of dict
    :type output_path: str
    '''

    try:
        file_perm = 'a' if os.path.isfile(output_path) else 'w'
        with open(output_path, file_perm) as file:
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
            raise Exception(
                f"Object type '{type(data)} is not supported. Must be list or dict")

        with open(output_path, "w") as file:
            for line in new_contents:
                file.write(line + "\n")
    except Exception as ex:
        raise ex


def get_last_id(bulk_api_path):
    '''
    Retreiving the last id from a JSON in bulk api format,
    will raise exception if file path doesn't exist
    :param bulk_api_path: File path to json in bulk api format
    :type bulk_api_path: str
    :raises Exception: Bulk API path does not exist
    :return last_id: The last id in the json
    :rtype last_id: int
    '''
    try:
        if not os.path.exists(bulk_api_path):
            raise Exception(f"The path: {bulk_api_path} does not exist")

        with open(bulk_api_path) as file:
            lines = file.read().splitlines()
            last_id = (json.loads(lines[-2]))["index"]["_id"]
            return last_id
    except Exception as ex:
        raise(ex)


def get_last_document(bulk_api_path):
    '''
    Retrieve the last document (row) from aa JSON in bulk api format,
    will raise exception if file path doesn't exist
    :param bulk_api_path: File path to json in bulk api format
    :type bulk_api_path: str
    :raises Exception: Bulk API path does not exist
    :return last_document: The row of information
    :rtype last_document: dict
    '''
    try:
        if not os.path.exists(bulk_api_path):
            raise Exception(f"The path: {bulk_api_path} does not exist")

        with open(bulk_api_path) as file:
            lines = file.read().splitlines()
            last_document = (json.loads(lines[-1]))
            return last_document
    except Exception as ex:
        raise(ex)


def get_files(path, pattern, recursive=False):
    '''
    This function returns a list of files that match a given pattern.
    :param path: Path to a directory
    :param regex: regex pattern to match files
    :param recursive: option to look for files recursively within a directory, default=False
    :type path: str
    :type pattern: str
    :type recursive: bool
    :raises Exception: path is not a directory, does not exist
    :return files: A list of found files, returning an empty list if nothing is found
    :rtype files: list
    '''
    try:
        files = []
        validate.is_dir(path)
        regex = re.compile(pattern)
        for file in os.listdir(path):
            full_path = os.path.join(path, file)
            __, extension = os.path.splitext(full_path)
            if os.path.isfile(full_path) and regex.match(file):
                files.append(full_path)
            elif os.path.isdir(full_path) and recursive:
                files.extend(get_files(full_path, pattern, recursive=True))
        return files
    except Exception as ex:
        raise(ex)


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
            current_index = get_last_id(output_path) + 1

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
                raise Exception(
                    f"Object type '{type(data)} is not supported. Must be list or dict")
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
