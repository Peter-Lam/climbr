#!/usr/bin/python3
'''
This module contains common used functions by scripts within Climbing-Tracker
'''
import base64
import codecs
import json
import os
import re
import requests
import shutil
import smtplib
import ssl
import sys
import urllib
import yaml
import common.validate as validate
import firebase_admin
from datetime import datetime
from dotenv import load_dotenv
from firebase_admin import credentials
from firebase_admin import firestore
from elasticsearch import Elasticsearch
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import config as config  # noqa


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


def connect_to_firestore():
    '''
    Establish connection to firestore using secrect service account credientials
    :return: firestore db instance
    '''
    # Use a service account from json file
    # For more information: https://firebase.google.com/docs/firestore/quickstart
    cred = credentials.Certificate(config.firestore_json)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db


def copy_file(src, dest, file_name=''):
    '''
    Copy a file from source to destination, if the file already exists, it will add _copy to the filename. Returns path of file destination if successful
    :param src: source path of file
    :param dest: destination path
    :param file_name: Optional way to change filename
    :type src: str
    :type dest: str
    :type file_name: str
    :return: file destination
    :rtype: str
    :raises Exception: path does not exist
    '''
    try:
        # Keeping track of duplicate files, and incrementing filename as needed
        duplicate = 0
        # Checking if paths exist
        if not os.path.exists(src) or not os.path.exists(dest):
            raise Exception(f"The file {src}, does not exist")
        else:
            # Set the destination path with filename if given otherwise use the source name
            dest_path = f"{os.path.join(dest, file_name)}" if file_name else os.path.join(
                dest, os.path.basename(src))
            # If the file already exists, then append _copy to the end
            while os.path.isfile(dest_path):
                file, ext = os.path.splitext(os.path.basename(dest_path))
                dest_path = os.path.join(os.path.dirname(
                    dest_path), f"{file}_copy{ext}")
                print(
                    f"Warning: `{dest_path}` already exists, creating `{dest_path}` instead...")
            # Copy file to destination with new name if file_name is not empty
            shutil.copyfile(src, dest_path)
            return dest_path
    except Exception as ex:
        raise ex


def create_index(es_url, index_name, mapping_path, silent=False, force=False):
    '''
    Create an Elasticsearch index (table) using a mapping to define field types
    :param es_url: url to Elasticsearch instance
    :param index_name: Name of index
    :param mapping_path: Path to a json
    :param silent: suppress print messages
    :param force: force delete existing index
    :type es_url: str
    :type index_name: str
    :type mapping_path: str
    :type silent: bool
    :type force: bool
    :raises Exception: path is not a directory, does not exist or Elasticsearch is not running
    '''
    try:
        # Connecting to Elasticsearch
        es = connect_to_es(es_url)
        # Check for old indexes
        if es.indices.exists(index_name):
            if force:
                if not silent:
                    print(f"Deleting index {index_name}...")
                es.indices.delete(index_name)
            else:
                valid_input = False
                while not valid_input:
                    value = input(
                        f"The following index, '{index_name}', already exists. Would you like you override the index? All data will be deleted. (y/N)\t").lower()
                    if value == 'y':
                        print(f"Deleting index {index_name}...")
                        es.indices.delete(index_name)
                        valid_input = True
                    if value == 'n':
                        print(f"Skipping index creation for '{index_name}'.")
                        return
        mapping = load_file(mapping_path)
        try:
            if not silent:
                print(f"Creating {index_name} index...")
            es.indices.create(index_name, body=mapping)
            if not silent:
                print(f"Successfully created {index_name} index!")
        except Exception as ex:
            raise Exception(
                f"Unable to create mapping from '{mapping_path}'.")
    except Exception as ex:
        raise ex


def create_index_pattern(kibana_url, index_name, silent=False, force=False):
    '''
    Create a general Kibana index pattern by calling a cURL command
    :param kibana_url: url to the Kibana instance
    :param index_name: Name of index
    :param silent: suppress print messages
    :param force: force delete existing patterns
    :type index_name: str
    :type mapping_path: str
    :type silent: bool
    :type force: bool
    :raises Exception: Unable to ping Kibana instance
    '''
    try:
        # Variables for API call
        timefields = {'bookings': 'retrieved_at',
                      'projects': 'session.date',
                      'counters': 'session.date',
                      'sessions': 'date'}
        timefield = f', "timeFieldName":"{timefields[index_name]}"' if index_name in timefields.keys(
        ) else ''
        headers = {'kbn-xsrf': 'true',
                   'Content-Type': 'application/json'}
        data = '{{ "attributes": {{ "title": "{}*" {}}} }}'.format(
            index_name, timefield)
        # Try to ping Kibana
        if requests.get(kibana_url).status_code != 200:
            raise Exception(
                f"Unable to ping Kibana instance located at '{kibana_url}'.")
        index_url = urllib.parse.urljoin(
            kibana_url, f"api/saved_objects/index-pattern/{index_name}")
        # Check for existing index patterns, ask user to delete if found
        if requests.get(index_url).status_code == 200:
            if force:
                if not silent:
                    print(f"Deleting index pattern,'{index_name}' ...")
                del_response = requests.delete(index_url, headers=headers)
                if del_response.status_code != 200:
                    raise Exception(
                        "{del_response} Unable to delete index pattern for 'index_name'.")
            else:
                valid_input = False
                while not valid_input:
                    value = input(
                        f"Found existing index pattern, '{index_name}', would you like to overwrite? (Y/n)\t").lower()
                    if value == 'y':
                        if not silent:
                            print(f"Deleting index pattern,'{index_name}' ...")
                        del_response = requests.delete(
                            index_url, headers=headers)
                        if del_response.status_code != 200:
                            raise Exception(
                                "{del_response} Unable to delete index pattern for 'index_name'.")
                        valid_input = True
                    # If no is selected, then just exit out of this function and skip
                    if value == 'n':
                        if not silent:
                            print(
                                f"Skipping index pattern creation for '{index_name}'...")
                            return
        # API call to create index pattern
        if not silent:
            print(f"Creating index pattern for '{index_name}'...")
        response = requests.post(
            index_url, headers=headers, data=data)
        if response.status_code == 200:
            if not silent:
                print(
                    f"Successfully created index pattern for '{index_name}'!")
        else:
            # TODO: Log respons output on error
            # response.json()
            raise Exception(
                f"{response} Unable to create bookings index pattern.")

    except Exception as ex:
        raise ex


def convert_grades(grade):
    # TODO: Convert climbing grades to normalize data
    # https://www.mec.ca/en/explore/climbing-grade-conversion
    raise Exception("TODO")


def convert_to_24_hour(time):
    '''
    Converting time string to 24 hour format, throwing an error if unexpected format
    :param time: time in 12 hour format
    :type time: str
    :raises Exception: Unexpected time format
    :return: Time in HH:MM AM/PM format
    :rtype: str
    '''
    try:
        # 24 hour time regex
        hh_mm = re.compile("^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")
        h_mm = re.compile("^([0-9]):[0-5][0-9]$")
        # Declaring regex pattens
        hh_mm_a = re.compile("^(1[0-2]|0[1-9]):[0-5][0-9] (AM|PM)$")
        h_mm_a = re.compile("^([1-9]):[0-5][0-9] (AM|PM)$")
        hh_a = re.compile("^(1[0-2]|0[1-9]) (AM|PM)$")
        h_a = re.compile("^[1-9] (AM|PM)$")
        if hh_mm_a.match(time) or h_mm_a.match(time):
            return datetime.strftime(datetime.strptime(time, "%I:%M %p"), "%H:%M")
        elif hh_a.match(time) or h_a.match(time):
            return datetime.strftime(datetime.strptime(time, "%I %p"), "%H:%M")
        elif hh_mm.match(time) or h_mm.match(time):
            return datetime.strftime(datetime.strptime(time, "%H:%M"), "%H:%M")
        else:
            raise Exception(
                f"Unexpected format. Unable to convert '{time}'to 24 hour format.")
    except Exception as ex:
        raise ex


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
        hh_mm_a = re.compile("^(1[0-2]|0[1-9]):[0-5][0-9] (AM|PM)$")
        h_mm_a = re.compile("^([1-9]):[0-5][0-9] (AM|PM)$")
        hh_a = re.compile("^(1[0-2]|0[1-9]) (AM|PM)$")
        h_a = re.compile("^[1-9] (AM|PM)$")
        # 24 hour time regex
        hh_mm = re.compile("^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")
        h_mm = re.compile("^([0-9]):[0-5][0-9]$")
        if hh_mm_a.match(time) or h_mm_a.match(time):
            return datetime.strftime(datetime.strptime(time, "%I:%M %p"), "%I:%M %p")
        elif hh_a.match(time) or h_a.match(time):
            return datetime.strftime(datetime.strptime(time, "%I %p"), "%I:%M %p")
        elif hh_mm.match(time) or h_mm.match(time):
            return datetime.strftime(datetime.strptime(time, "%H:%M"), "%I:%M %p")
        else:
            raise Exception(
                f"Unexpected format. Unable to convert '{time}'to HH:MM AM/PM format.")
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


def export_kibana(kibana_url, output, silent=False, force=False):
    '''
    Exporting all Kibana objects into ndjson by calling a cURL command
    :param kibana_url: url to the Kibana instance
    :param output: full path of output file for ndjson
    :param silent: suppress print messages
    :param force: force delete existing index
    :type kibana_url: str
    :type output: str
    :type silent: bool
    :type force: bool
    :raises Exception: Unable to ping Kibana instance
    '''
    try:
        # Variables
        dashboard_ids, output_data = [], []
        headers = {'kbn-xsrf': 'true', 'Content-Type': 'application/json'}
        data = {"objects": [], "includeReferencesDeep": True}
        export_url = urllib.parse.urljoin(
            kibana_url, f"api/saved_objects/_export")
        find_url = urllib.parse.urljoin(
            kibana_url, f"api/saved_objects/_find")
        # Try to ping Kibana
        if requests.get(kibana_url).status_code != 200:
            raise Exception(
                f"Unable to ping Kibana instance located at '{kibana_url}'")

        # If the file already exists, prompt user about deletion
        if os.path.isfile(output):
            valid = True if force else False
            while not valid:
                user_response = input(
                    f"A file already exists at '{output}', would you like to overwrite? (Y/n)\t").lower()
                if user_response == 'y':
                    valid = True
                    if not silent:
                        print(f"Overwriting file located at '{output}'...")
                if user_response == 'n':
                    raise Exception(
                        f"File already exists at '{output}', please chose a different name using the '-o' argument or delete the existing file and try again.")
        # Get all dashboard ids to export
        if not silent:
            print(f"Retrieving dashboards and related objects...")
        dashboards = requests.get(find_url, params={'type': 'dashboard'}).json()[
            'saved_objects']
        for dashboard in dashboards:
            dashboard_ids.append(dashboard['id'])
            data['objects'].append(
                {"type": "dashboard", "id": dashboard['id']})
        data = str(data).replace("True", "true").replace('\'', '\"')
        # Exporting dashboards and related objects
        if not silent:
            print(f"Exporting Kibana dashboard and objects...")
        response = requests.post(
            export_url, headers=headers, data=data)
        if response.status_code == 200:
            try:
                with open(output, "w") as file:
                    file.write(response.text)
                if not silent:
                    print(f"Successfully exported!")
            except Exception as ex:
                raise Exception(
                    f"Unable to write to '{output}'. The file may be open in another program, please ensure all related files are closed and try again.")
        else:
            raise Exception(f"{response} Unable to export")

    except Exception as ex:
        raise ex


def get_last_id(bulk_api_path):
    '''
    Retreiving the last id from a JSON in bulk api format,
    will raise exception if file path doesn't exist
    : param bulk_api_path: File path to json in bulk api format
    : type bulk_api_path: str
    : raises Exception: Bulk API path does not exist
    : return last_id: The last id in the json
    : rtype last_id: int
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
    Retrieve the last document(row) from aa JSON in bulk api format,
    will raise exception if file path doesn't exist
    : param bulk_api_path: File path to json in bulk api format
    : type bulk_api_path: str
    : raises Exception: Bulk API path does not exist
    : return last_document: The row of information
    : rtype last_document: dict
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
    : param path: Path to a directory
    : param pattern: regex pattern to match files
    : param recursive: option to look for files recursively within a directory, default = False
    : type path: str
    : type pattern: str
    : type recursive: bool
    : raises Exception: path is not a directory, does not exist
    : return files: A list of found files, returning an empty list if nothing is found
    : rtype files: list
    '''
    try:
        files = []
        validate.directory(path)
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


def import_env(path):
    '''
    Get and set environment variables from an .env file
    :param path: path to .env file
    :type path: str
    :raises Exception: Unable to find .env file at '{path}'.
    '''
    try:
        # Load environment variables from given path
        if os.path.isfile(path):
            load_dotenv(path)
        else:
            raise Exception(f"Unable to find .env file at '{path}'.")
    except Exception as ex:
        raise ex


def import_kibana(kibana_url, ndjson, silent=False):
    '''
    Import all Kibana objects using ndjson and api command
    : param kibana_url: url to the Kibana instance
    : param ndjson: path to ndjson file
    : param silent: suppress print messages
    : type kibana_url: str
    : type ndjson: str
    : type silent: bool
    : raises Exception: Unable to ping Kibana instance
    '''
    try:
        if not silent:
            print(f"Importing Kibana dashboard and objects from '{ndjson}'...")
        # Try to ping Kibana
        if requests.get(kibana_url).status_code != 200:
            raise Exception(
                f"Unable to ping Kibana instance located at '{kibana_url}'")
        url = urllib.parse.urljoin(
            kibana_url, f"api/saved_objects/_import")
        headers = {'kbn-xsrf': 'true'}
        files = {'file': ('request.ndjson', load_file(ndjson))}
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            if not silent:
                print(f"Successfully imported!")
        else:
            # TODO: Log respons output on error
            raise Exception(
                f"{response} Unable to import")

    except Exception as ex:
        raise ex


def load_bulk_json(path):
    '''
    Opens bulk json and loads as a dict
    : param path: Path to regular json file to be converted
    : type path: path
    : return: Returns file contents
    : rtype: dict
    : raises Exception: JSON path does not exist
    '''
    if not os.path.exists(path):
        raise Exception(f"The path: {path} does not exist")
    with open(path, 'r') as file:
        file_contents = file.read().splitlines()
    new_contents = []
    for line in file_contents:
        if "{\"index\":" not in line:
            new_contents.append(json.loads(line))
    return new_contents


def load_json(path):
    '''
    Opens and loads a JSON file
    : param path: Path to JSON
    : type path: str
    : raises Exception: JSON path does not exist
    : return: File contents
    : rtype: json
    '''
    if os.path.exists(path):
        raise Exception(f"The path: {path} does not exist")
    with open(path, 'r') as file:
        return json.load(file)


def load_yaml(path):
    '''
    Reads a yaml climbing log file and returns the object
    : param path: Path to yaml
    : type path: str
    : raises Exception: Yaml path does not exist
    : return: Config contents
    : rtype: yaml
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
    : param path: Path to file
    : type path: str
    : raises Exception: file path does not exist
    : return: file contents
    : rtype: str
    '''
    try:
        if not os.path.exists(path):
            raise Exception(f"The path: {path} does not exist")
        with open(path, 'r') as file:
            return file.read()
    except Exception as ex:
        raise Exception(f"Unable to read file: {path}")


def send_email(sender, sender_pass, receiver, subject, template_dir, message, attachments=None):
    '''
    Send a email to a recipient with a html formatted message. Used to automate error notification
    :param sender: senders email
    :param sender_pass: senders password used to send email on behalf of user
    :param receiver: destination email
    :param message: message to be included in the email, in html format
    :param attachments: paths to attachments
    :type sender: str
    :type sender_pass: str
    :type receiver: str
    :type message: str
    :type attachments: list of str
    '''
    try:
        # Verifying emails, will throw Exception if not valid
        validate.email(sender)
        validate.email(receiver)
        # Create a secure SSL context
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
            # Logging in
            server.login(sender, sender_pass)
            # Create email with formatting
            msg = MIMEMultipart("alternative")
            # Email Params
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = receiver

            # # Read HTML and replace filler text with message
            template = codecs.open(
                get_files(template_dir, ".*\.html$", recursive=False).pop())
            template = str(template.read()).replace("REPLACE_ME", message).replace(
                "DATETIME_HERE", str(datetime.now().isoformat()))
            # Embedding all relating images
            images = get_files(os.path.join(template_dir, 'images'), ".*")
            for img in images:
                filename, __ = os.path.splitext(os.path.basename(img))
                msg.attach(MIMEText(template, "html"))
                fp = open(img, "rb")
                image = MIMEImage(fp.read())
                fp.close()
                image.add_header('Content-ID', f'<{filename}>')
                msg.attach(image)
            # If there are attachments, then add them to the email
            if attachments:
                for filepath in attachments:
                    filename = os.path.basename(filepath)
                    # Open the file as binary mode
                    attach_file = open(filepath, 'rb')
                    payload = MIMEBase('application', 'octate-stream')
                    payload.set_payload((attach_file).read())
                    encoders.encode_base64(payload)  # encode the attachment
                    # add payload header with filename
                    payload.add_header('Content-Decomposition',
                                       f"attachment; filename= {filename}")
                    msg.attach(payload)
            # Send email
            server.sendmail(sender, receiver, msg.as_string())
        print(f"'{subject}' was sent to : {receiver}")
    except Exception as ex:
        raise Exception(f"Unable to send email to {receiver}:\n{ex}")


def str_to_time(string):
    '''
    Coverting time string to a datetime object, throwing an error if unexpected format
    : param time: time in 12 or 24 hour format
    : type time: str
    : raises Exception: Unexpected time format
    : return: datetime object
    : rtype: datetime
    '''
    try:
        # Declaring regex pattens
        hh_mm_a = re.compile("^(1[0-2]|0[1-9]):[0-5][0-9] (AM|PM)$")
        h_mm_a = re.compile("^([1-9]):[0-5][0-9] (AM|PM)$")
        hh_a = re.compile("^(1[0-2]|0[1-9]) (AM|PM)$")
        h_a = re.compile("^[1-9] (AM|PM)$")
        # 24 hour time regex
        hh_mm = re.compile("^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")
        h_mm = re.compile("^([0-9]):[0-5][0-9]$")
        if hh_mm_a.match(string) or h_mm_a.match(string):
            return datetime.strptime(string, "%I:%M %p")
        elif hh_a.match(string) or h_a.match(string):
            return datetime.strptime(string, "%I %p")
        elif hh_mm.match(string) or h_mm.match(string):
            return datetime.strptime(string, "%H:%M")
        # TODO: Convert 24 hour format to 12 hour
        else:
            raise Exception(
                f"Unexpected format. Unable to convert '{string}'to HH:MM AM/PM format.")
    except Exception as ex:
        raise ex


def update_bulk_api(data, output_path, index_name):
    '''
    Updating an existing json in bulk api format with new ioc information,
    will raise exception if file path doesn't exist
    : param data: Information that is to be added to the json
    : param output_path: The path to the json in bulk api format
    : param index_name: Index name for elasticsearch
    : raises Exception: Output path does not exist
    : type data: list of dict
    : type output_path: str
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


def upload_to_es(es_url, path, recursive=False, silent=False):
    '''
    Upload bulk json files into Elasticsearch
    : param es_url: url to Elasticsearch instance
    : param path: path to directory to import OR path to a specific file
    : param recursive: optional bool to collect files from sub-dirs
    : param silent: suppres print messages
    : type es_url: str
    : type path: str
    : type recursive: bool
    : type silent: bool
    : raises Exception: path is not a directory, does not exist
    '''
    try:
        # Connecting to Elasticsearch
        es = connect_to_es(es_url)
        # Load all json files located in output dir into ES
        bulk_json = []
        try:
            validate.file(path)
            bulk_json.append(path)
        except Exception:
            bulk_json = get_files(path, ".*\.json$")
            if not bulk_json:
                raise Exception(
                    f"Unable to find files to upload, please use 'climb.py update' first then re-run 'climb.py show'")

        for file in bulk_json:
            content = load_file(file)
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
                raise Exception(
                    f"Unable to upload '{file}' into Elasticsearch do to the following rows:\n{es_error}")
            elif not silent:
                print(f"'{file}' has been successfully uploaded!")
    except Exception as ex:
        raise ex


def write_bulk_api(data, output_path, index_name):
    '''
    Writes to a json file in bulk api format given a list of information,
    if the output path already exists, will overwrite
    : param data: data to add write to json
    : param output_path: the path to the json in bulk api format
    : param index_name: Index name for elasticsearch
    : type data: list of dict
    : type output_path: str
    : type index_name: str
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


def write_json(data, output_path):
    '''
    Reads values and writes into output file path,
    : param data: data to add write to json
    : param output_path: Output path including filename.json
    : type data: list of dict
    : type output_path: str
    '''

    try:
        with open(output_path, w) as file:
            json.dump(data, file, indent=4)
    except Exception as ex:
        raise ex


def write_log(log, output_path):
    '''
    Writing to log file, will create file and parent folder if the path doesn't exist
    : param log: Log information
    : param output_path: path to log file
    : type log: str
    : type output_path: str
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


def write_yaml(data, output_path, force=False, silent=False):
    '''
    Reads values and writes into output file path,
    if the output path already exists, will overwrite if force is True
    : param data: data to add write to yaml
    : param output_path: Output path including filename.yaml
    : type data: list of dict
    : type output_path: path
    '''

    try:
        if os.path.exists(output_path):
            if force:
                if not silent:
                    print(f"Overwriting existing file: '{output_path}'")
            else:
                valid_input = False
                while not valid_input:
                    value = input(
                        f"The following file, '{output_path}', already exists. Would you like you override the file? All data will be deleted. (y/N)\t").lower()
                    if value == 'y':
                        print(f"Overwriting existing file: '{output_path}'")
                        valid_input = True
                    if value == 'n':
                        print(
                            f"Not overwriting. Please try again with a unique filename.")
                        sys.exit(1)
        with open(output_path, 'w') as f:
            data = yaml.safe_dump(data, f, sort_keys=False,
                                  default_flow_style=False)
    except Exception as ex:
        raise ex
