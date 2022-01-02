#!/usr/bin/python3
"""This module contains common used functions by scripts within Climbing-Tracker."""
import codecs
import json
import os
import re
import shutil
import smtplib
import sys
import urllib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import firebase_admin
import requests
import yaml
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from firebase_admin import credentials, firestore
from loguru import logger

import common.validate as validate

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import config as config  # noqa


def connect_to_es(es_url):
    """
    Connect to Elasticsearch and return ES object.

    Raises exception if unable to ping.

    :param es_url: url to the Elasticsearch instance
    :type: str
    :return: ES Instance
    :rtype: obj
    :raises Exception: Elasticsearch is not running
    """
    es = Elasticsearch([es_url], verify_certs=True)
    if not es.ping():
        logger.error(
            "Unable to ping Elasticsearch, please confirm connection and try again."
        )
        sys.exit(1)
    return es


def connect_to_firestore():
    """
    Connect to firestore using secrect service account credientials.

    :return: firestore db instance
    """
    # Use a service account from json file
    # For more information: https://firebase.google.com/docs/firestore/quickstart
    cred = credentials.Certificate(config.firestore_json)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db


def copy_file(src, dest, file_name=""):
    """
    Copy a file from source to destination.

    If the file already exists, it will add _copy to the filename.
    Returns path of file destination if successful.

    :param src: source path of file
    :param dest: destination path
    :param file_name: Optional way to change filename
    :type src: str
    :type dest: str
    :type file_name: str
    :return: file destination
    :rtype: str
    :raises Exception: path does not exist
    """
    # Keeping track of duplicate files, and incrementing filename as needed
    # Checking if paths exist
    if not os.path.exists(src) or not os.path.exists(dest):
        logger.error(f"The file {src}, does not exist")
        sys.exit(1)
    else:
        # Set the dest path with filename if given otherwise use the source name
        dest_path = (
            f"{os.path.join(dest, file_name)}"
            if file_name
            else os.path.join(dest, os.path.basename(src))
        )
        # If the file already exists, then append _copy to the end
        while os.path.isfile(dest_path):
            file, ext = os.path.splitext(os.path.basename(dest_path))
            dest_path = os.path.join(os.path.dirname(dest_path), f"{file}_copy{ext}")
            logger.warning(
                f"Warning: `{dest_path}` already exists,"
                f" creating `{dest_path}` instead..."
            )
        # Copy file to destination with new name if file_name is not empty
        shutil.copyfile(src, dest_path)
        return dest_path


def create_index(es_url, index_name, mapping_path, force=False):
    """
    Create an Elasticsearch index (table) using a mapping to define field types.

    :param es_url: url to Elasticsearch instance
    :param index_name: Name of index
    :param mapping_path: Path to a json
    :param force: force delete existing index
    :type es_url: str
    :type index_name: str
    :type mapping_path: str
    :type force: bool
    :raises Exception: path is not a dir, does not exist or Elasticsearch is not running
    """
    # Connecting to Elasticsearch
    es = connect_to_es(es_url)
    # Check for old indexes
    if es.indices.exists(index_name):
        if force:
            logger.debug(f"Deleting index {index_name}...")
            es.indices.delete(index_name)
        else:
            valid_input = False
            while not valid_input:
                question = (
                    f"The following index, '{index_name}', already exists."
                    f" Would you like you override the index?"
                    " All data will be deleted. (y/N)\t"
                )
                value = input(question).lower()
                logger.debug(f"{question} {value}")
                if value == "y":
                    logger.info(f"Deleting index {index_name}...")
                    es.indices.delete(index_name)
                    valid_input = True
                if value == "n":
                    logger.debug(f"Skipping index creation for '{index_name}'.")
                    return
    mapping = load_file(mapping_path)
    try:
        logger.debug(f"Creating {index_name} index...")
        es.indices.create(index_name, body=mapping)
        logger.debug(f"Successfully created {index_name} index!")
    except Exception:
        logger.error(f"Unable to create ElasticSearch mapping from '{mapping_path}'.")
        sys.exit(1)


def create_index_pattern(kibana_url, index_name, force=False):
    """
    Create a Kibana index pattern by calling a cURL command.

    :param kibana_url: url to the Kibana instance
    :param index_name: Name of index
    :param force: force delete existing patterns
    :type index_name: str
    :type mapping_path: str
    :type force: bool
    :raises Exception: Unable to ping Kibana instance
    """
    # Variables for API call
    timefields = {
        "bookings": "retrieved_at",
        "projects": "session.date",
        "counters": "session.date",
        "sessions": "date",
    }
    timefield = (
        f', "timeFieldName":"{timefields[index_name]}"'
        if index_name in timefields.keys()
        else ""
    )
    headers = {"kbn-xsrf": "true", "Content-Type": "application/json"}
    data = '{{ "attributes": {{ "title": "{}*" {}}} }}'.format(index_name, timefield)
    # Try to ping Kibana
    if requests.get(kibana_url).status_code != 200:
        logger.error(f"Unable to ping Kibana instance located at '{kibana_url}'.")
        sys.exit(1)
    index_url = urllib.parse.urljoin(
        kibana_url, f"api/saved_objects/index-pattern/{index_name}"
    )
    # Check for existing index patterns, ask user to delete if found
    if requests.get(index_url).status_code == 200:
        if force:
            logger.debug(f"Deleting index pattern,'{index_name}' ...")
            del_response = requests.delete(index_url, headers=headers)
            if del_response.status_code != 200:
                logger.error(f"Unable to delete index pattern for '{index_name}'.")
                logger.error(del_response)
                sys.exit(1)

        else:
            valid_input = False
            while not valid_input:
                question = (
                    f"Found existing index pattern, '{index_name}',"
                    " would you like to overwrite? (Y/n)\t"
                )
                value = input(question).lower()
                logger.debug(f"{question} {value}")
                if value == "y":
                    logger.info(f"Deleting index pattern,'{index_name}' ...")
                    del_response = requests.delete(index_url, headers=headers)
                    if del_response.status_code != 200:
                        logger.error(
                            f"Unable to delete index pattern for '{index_name}'."
                        )
                        logger.error(del_response)
                        sys.exit(1)
                    valid_input = True
                # If no is selected, then just exit out of this function and skip
                if value == "n":
                    logger.info(
                        f"Skipping index pattern creation for '{index_name}'..."
                    )
                    return
    # API call to create index pattern
    logger.debug(f"Creating index pattern for '{index_name}'...")
    response = requests.post(index_url, headers=headers, data=data)
    if response.status_code == 200:
        logger.debug(f"Successfully created index pattern for '{index_name}'!")
    else:
        logger.error(
            f"Unable to create Kibana index for {index_name}. See log for more details."
        )
        logger.debug(response.json())
        sys.exit(1)


def convert_to_24_hour(time):
    """
    Convert time string to 24 hour format.

    Raises an error if unexpected format.

    :param time: time in 12 hour format
    :type time: str
    :raises Exception: Unexpected time format
    :return: Time in HH:MM AM/PM format
    :rtype: str
    """
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
        logger.error(f"Unexpected format. Unable to convert '{time}'to 24 hour format.")
        sys.exit(1)


def convert_to_hhmm(time):
    """
    Coverts time string to HH:MM AM/PM format.

    Raises an error if unexpected format.
    :param time: time in 12 hour format
    :type time: str
    :raises Exception: Unexpected time format
    :return: Time in HH:MM AM/PM format
    :rtype: str
    """
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
        logger.error(
            f"Unexpected format. Unable to convert '{time}'to HH:MM AM/PM format."
        )
        sys.exit(1)


def delete_file(path):
    """
    Delete file if it exists.

    :param path: Path of file
    :type: str
    """
    if os.path.exists(path):
        os.remove(path)


def export_kibana(kibana_url, output, force=False):
    """
    Export Kibana objects into ndjson by calling a cURL command.

    :param kibana_url: url to the Kibana instance
    :param output: full path of output file for ndjson
    :param force: force delete existing index
    :type kibana_url: str
    :type output: str
    :type force: bool
    :raises Exception: Unable to ping Kibana instance
    """
    # Variables
    dashboard_ids = []
    headers = {"kbn-xsrf": "true", "Content-Type": "application/json"}
    data = {"objects": [], "includeReferencesDeep": True}
    export_url = urllib.parse.urljoin(kibana_url, "api/saved_objects/_export")
    find_url = urllib.parse.urljoin(kibana_url, "api/saved_objects/_find")
    # Try to ping Kibana
    if requests.get(kibana_url).status_code != 200:
        logger.error(f"Unable to ping Kibana instance located at '{kibana_url}'")
        sys.exit(1)

    # If the file already exists, prompt user about deletion
    if os.path.isfile(output):
        valid = True if force else False
        while not valid:
            question = (
                f"A file already exists at '{output}',"
                " would you like to overwrite? (Y/n)\t"
            )
            user_response = input(question).lower()
            logger.debug(f"{question} {user_response}")
            if user_response == "y":
                valid = True
                logger.info(f"Overwriting file located at '{output}'...")
            if user_response == "n":
                logger.warning(
                    f"File already exists at '{output}',"
                    " please chose a different name using the '-o' argument"
                    " or delete the existing file and try again."
                )
                sys.exit(1)
    # Get all dashboard ids to export
    logger.info("Retrieving dashboards and related objects...")
    dashboards = requests.get(find_url, params={"type": "dashboard"}).json()[
        "saved_objects"
    ]
    for dashboard in dashboards:
        dashboard_ids.append(dashboard["id"])
        data["objects"].append({"type": "dashboard", "id": dashboard["id"]})
    data = str(data).replace("True", "true").replace("'", '"')
    # Exporting dashboards and related objects
    logger.info("Exporting Kibana dashboard and objects...")
    response = requests.post(export_url, headers=headers, data=data)
    if response.status_code == 200:
        try:
            with open(output, "w") as file:
                file.write(response.text)
            logger.info(f"Successfully exported files to '{output}'")
        except Exception:
            logger.error(
                f"Unable to write to '{output}'."
                " The file may be open in another program,"
                " please ensure all related files are closed and try again."
            )
            sys.exit(1)
    else:
        logger.error("Unable to export Kibana index. See log for more details.")
        logger.debug(response.json())
        sys.exit(1)


def get_last_id(bulk_api_path):
    """
    Retrieve the last id from a JSON in bulk api format.

    Raise exception if file path doesn't exist.

    : param bulk_api_path: File path to json in bulk api format
    : type bulk_api_path: str
    : raises Exception: Bulk API path does not exist
    : return last_id: The last id in the json
    : rtype last_id: int
    """
    if not os.path.exists(bulk_api_path):
        logger.error(f"The path: '{bulk_api_path}' does not exist")
        sys.exit(1)

    with open(bulk_api_path) as file:
        lines = file.read().splitlines()
        last_id = (json.loads(lines[-2]))["index"]["_id"]
        return last_id


def get_last_document(bulk_api_path):
    """
    Retrieve the last document(row) from bulk json.

    Raises exception if file path doesn't exist.

    : param bulk_api_path: File path to json in bulk api format
    : type bulk_api_path: str
    : raises Exception: Bulk API path does not exist
    : return last_document: The row of information
    : rtype last_document: dict
    """
    if not os.path.exists(bulk_api_path):
        logger.erorr(f"The path: '{bulk_api_path}' does not exist")
        sys.exit()

    with open(bulk_api_path) as file:
        lines = file.read().splitlines()
        last_document = json.loads(lines[-1])
        return last_document


def get_files(path, pattern, recursive=False):
    """
    Return a list of files that match a given pattern.

    : param path: Path to a directory
    : param pattern: regex pattern to match files
    : param recursive: option to look for files recursively within a directory
    : type path: str
    : type pattern: str
    : type recursive: bool
    : raises Exception: path is not a directory, does not exist
    : return files: A list of found files, returning an empty list if nothing is found
    : rtype files: list
    """
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


def import_env(path):
    """
    Get and set environment variables from an .env file.

    :param path: path to .env file
    :type path: str
    :raises Exception: Unable to find .env file at '{path}'.
    """
    if os.path.isfile(path):
        load_dotenv(path)
    else:
        logger.error(f"Unable to find .env file at '{path}'.")
        sys.exit(1)


def import_kibana(kibana_url, ndjson):
    """
    Import all Kibana objects using ndjson and api command.

    : param kibana_url: url to the Kibana instance
    : param ndjson: path to ndjson file
    : type kibana_url: str
    : type ndjson: str
    : raises Exception: Unable to ping Kibana instance
    """
    logger.info(f"Importing Kibana dashboard and objects from '{ndjson}'...")
    # Try to ping Kibana
    if requests.get(kibana_url).status_code != 200:
        logger.error(f"Unable to ping Kibana instance located at '{kibana_url}'")
        sys.exit(1)
    url = urllib.parse.urljoin(kibana_url, "api/saved_objects/_import")
    headers = {"kbn-xsrf": "true"}
    files = {"file": ("request.ndjson", load_file(ndjson))}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        logger.info("Successfully imported!")
    else:
        logger.error("Unable to import Kibana objects. See log for more details.")
        logger.debug(response.json())
        sys.exit(1)


def load_bulk_json(path):
    """
    Load build json as a dict.

    : param path: Path to regular json file to be converted
    : type path: path
    : return: Returns file contents
    : rtype: dict
    : raises Exception: JSON path does not exist
    """
    if not os.path.exists(path):
        logger.error(f"The path: {path} does not exist")
        sys.exit(1)
    with open(path, "r") as file:
        file_contents = file.read().splitlines()
    new_contents = []
    for line in file_contents:
        if '{"index":' not in line:
            new_contents.append(json.loads(line))
    return new_contents


def load_json(path):
    """
    Load a JSON file.

    : param path: Path to JSON
    : type path: str
    : raises Exception: JSON path does not exist
    : return: File contents
    : rtype: json
    """
    if os.path.exists(path):
        logger.error(f"The path: {path} does not exist")
        sys.exit(1)
    with open(path, "r") as file:
        return json.load(file)


def load_yaml(path):
    """
    Read a yaml climbing log file and returns the object.

    : param path: Path to yaml
    : type path: str
    : raises Exception: Yaml path does not exist
    : return: Config contents
    : rtype: yaml
    """
    try:
        if not os.path.exists(path):
            logger.error(f"The path: {path} does not exist")
            sys.exit(1)
        with open(path, "r") as stream:
            return yaml.safe_load(stream)
    except Exception as ex:
        logger.error(f"Unable to read climbing log, formatting error found {ex}")
        sys.exit(1)


def load_file(path):
    """
    Read the contents of a file and returns a string with contents.

    : param path: Path to file
    : type path: str
    : raises Exception: file path does not exist
    : return: file contents
    : rtype: str
    """
    try:
        if not os.path.exists(path):
            logger.error(f"The path: {path} does not exist")
            sys.exit(1)
        with open(path, "r") as file:
            return file.read()
    except Exception:
        logger.error(f"Unable to read file: {path}")
        sys.exit(1)


def send_email(
    sender, sender_pass, receiver, subject, template_dir, message, attachments=None
):
    """
    Send a email to a recipient with a html formatted message.

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
    """
    try:
        # Verifying emails, will throw Exception if not valid
        validate.email(sender)
        validate.email(receiver)
        # Create a secure SSL context
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            # Logging in
            server.login(sender, sender_pass)
            # Create email with formatting
            msg = MIMEMultipart("alternative")
            # Email Params
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = receiver

            # # Read HTML and replace filler text with message
            template = codecs.open(
                get_files(template_dir, r".*\.html$", recursive=False).pop()
            )
            template = (
                str(template.read())
                .replace("REPLACE_ME", message)
                .replace("DATETIME_HERE", str(datetime.now().isoformat()))
            )
            # Embedding all relating images
            images = get_files(os.path.join(template_dir, "images"), ".*")
            for img in images:
                filename, __ = os.path.splitext(os.path.basename(img))
                msg.attach(MIMEText(template, "html"))
                fp = open(img, "rb")
                image = MIMEImage(fp.read())
                fp.close()
                image.add_header("Content-ID", f"<{filename}>")
                msg.attach(image)
            # If there are attachments, then add them to the email
            if attachments:
                for filepath in attachments:
                    filename = os.path.basename(filepath)
                    # Open the file as binary mode
                    attach_file = open(filepath, "rb")
                    payload = MIMEBase("application", "octate-stream")
                    payload.set_payload((attach_file).read())
                    encoders.encode_base64(payload)  # encode the attachment
                    # add payload header with filename
                    payload.add_header(
                        "content-disposition", "attachment", filename=filename
                    )
                    msg.attach(payload)
            # Send email
            server.sendmail(sender, receiver, msg.as_string())
        logger.info(f"'{subject}' was sent to : {receiver}")
    except Exception as ex:
        logger.debug(ex)
        logger.error(f"Unable to send email to {receiver}. See log for more details.")
        sys.exit(1)


def str_to_time(string):
    """
    Convert time string to datatime object.

    : param time: time in 12 or 24 hour format
    : type time: str
    : raises Exception: Unexpected time format
    : return: datetime object
    : rtype: datetime
    """
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
        logger.error(
            f"Unexpected format. Unable to convert '{string}' to HH:MM AM/PM format."
        )
        sys.exit(1)


def update_bulk_api(data, output_path, index_name):
    """
    Update an existing bulk api file.

    Raises exception if file path doesn't exist.

    : param data: Information that is to be added to the json
    : param output_path: The path to the json in bulk api format
    : param index_name: Index name for elasticsearch
    : raises Exception: Output path does not exist
    : type data: list of dict
    : type output_path: str
    """
    # Create a new file if it doesn't exist
    if not os.path.exists(output_path):
        logger.info(f"'{output_path}' not found, creating file and writing...")
        write_bulk_api(data, output_path, index_name)
    elif data:
        updated_list = []
        current_index = get_last_id(output_path) + 1

        # If the data is a dict, then assume it's one object
        if type(data) is dict:
            updated_list.append(
                json.dumps({"index": {"_index": index_name, "_id": current_index}})
            )
            updated_list.append(json.dumps(data))
            current_index += 1
        # If it's a list then, then assume it's multiple
        elif type(data) is list:
            for value in data:
                updated_list.append(
                    json.dumps({"index": {"_index": index_name, "_id": current_index}})
                )
                updated_list.append(json.dumps(value))
                current_index += 1
        else:
            logger.error(
                f"Object type '{type(data)} is not supported. Must be list or dict"
            )
            sys.exit(1)
        # Write to the JSON file
        with open(output_path, "a") as file:
            for line in updated_list:
                file.write(line + "\n")


def upload_to_es(es_url, path):
    """
    Upload bulk json files into Elasticsearch.

    : param es_url: url to Elasticsearch instance
    : param path: path to directory to import OR path to a specific file
    : type es_url: str
    : type path: str
    : raises Exception: path is not a directory, does not exist
    """
    # Connecting to Elasticsearch
    es = connect_to_es(es_url)
    # Load all json files located in output dir into ES
    bulk_json = []
    if os.path.isfile(path):
        bulk_json.append(path)
    else:
        bulk_json = get_files(path, r".*\.json$")
        if not bulk_json:
            logger.error(f"Unable to find files to upload in `{path}`")
            sys.exit(1)

    for file in bulk_json:
        content = load_file(file)
        es_response = es.bulk(content)
        # If there are errors, look for problematic index and alert user
        if es_response["errors"]:
            es_error = ""
            for item in es_response["items"]:
                if item["index"]["status"] != 200:
                    id = item["index"]["_id"]
                    exception_type = item["index"]["error"]["type"]
                    reason = item["index"]["error"]["reason"]
                    es_error += f"  [id:{id}] {exception_type}: {reason} \n"
            logger.error(
                f"Unable to upload '{file}' into Elasticsearch do to"
                f" the following rows:\n{es_error}"
            )
            sys.exit(1)
        logger.debug(f"'{file}' has been successfully uploaded!")


def write_bulk_api(data, output_path, index_name):
    """
    Write data in bulk api format.

    If the output path already exists, tge file will be overwritten.

    : param data: data to add write to json
    : param output_path: the path to the json in bulk api format
    : param index_name: Index name for elasticsearch
    : type data: list of dict
    : type output_path: str
    : type index_name: str
    """
    new_contents = []
    current_index = 0
    # If the data is a dict, then assume it's one object
    if type(data) is dict:
        new_contents.append(
            json.dumps({"index": {"_index": index_name, "_id": current_index}})
        )
        new_contents.append(json.dumps(data))
    # If it's a list then, then assume it's multiple
    elif type(data) is list:
        for row in data:
            new_contents.append(
                json.dumps({"index": {"_index": index_name, "_id": current_index}})
            )
            current_index += 1
            new_contents.append(json.dumps(row))
    else:
        logger.error(
            f"Object type '{type(data)} is not supported. Must be list or dict"
        )
        sys.exit(1)
    with open(output_path, "w") as file:
        for line in new_contents:
            file.write(line + "\n")


def write_json(data, output_path):
    """
    Write data to JSON.

    : param data: data to add write to json
    : param output_path: Output path including filename.json
    : type data: list of dict
    : type output_path: str
    """
    with open(output_path, "w") as file:
        json.dump(data, file, indent=4)


def write_log(log, output_path):
    """
    Write data to log file.

    Creates file and parent folder if the path doesn't exist.

    : param log: Log information
    : param output_path: path to log file
    : type log: str
    : type output_path: str
    """
    dirname = os.path.dirname(output_path)
    if not os.path.exists(dirname):
        logger.info(f"{dirname} does not exist, creating folder")
        os.makedirs(os.path.dirname(output_path))
    file_perm = "a" if os.path.isfile(output_path) else "w"
    with open(output_path, file_perm) as file:
        file.write(log + "\n")


def write_yaml(data, output_path, force=False):
    """
    Write to yaml file.

    If the output path already exists, will overwrite if force is True.

    : param data: data to add write to yaml
    : param output_path: Output path including filename.yaml
    : type data: list of dict
    : type output_path: path
    """
    if os.path.exists(output_path):
        if force:
            logger.debug(f"Overwriting existing file: '{output_path}'")
        else:
            valid_input = False
            while not valid_input:
                question = (
                    f"The following file, '{output_path}', already exists."
                    " Would you like you override the file?"
                    " All data will be deleted. (y/N)\t"
                )
                value = input(question).lower()
                logger.debug(f"{question} {value}")
                if value == "y":
                    logger.info(f"Overwriting existing file: '{output_path}'")
                    valid_input = True
                if value == "n":
                    logger.warning(
                        "Not overwriting. Please try again with a unique name."
                    )
                    sys.exit(1)
    with open(output_path, "w") as f:
        data = yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
