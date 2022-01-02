#!/usr/bin/python3
"""The core logic behind tracking climbing sessions and stats."""
import os
import sys
from datetime import datetime
from time import sleep

import requests
from loguru import logger

import common.args as cmd_args
import common.common as common
import common.globals as glbs
import common.validate as validate
import config as config
from common.session import Session


def error_callback(message):
    """
    Send an email notification about a given error.

    :param message:
    :type: loguru.Message
    """
    if config.smpt_email and config.smpt_pass and config.to_notify:
        logger.info(
            "An error has occured in climbr, "
            f"attempting to send notification to '{config.to_notify}'"
        )
        common.send_email(
            config.smpt_email,
            config.smpt_pass,
            config.to_notify,
            f"[{str(datetime.now())}] Climbr Error: climbr.py",
            os.path.join(glbs.EMAIL_TEMPLATE_DIR, "error_notification"),
            message,
            common.get_files(glbs.LOG_DIR, "climbr.log"),
        )
    else:
        logger.info(
            "Email credentials not found - unable to send email about error. "
            "See log file for error details instead."
        )
    sys.exit(1)


# Logging
logger.remove()
# System out
stdout_fmt = "<level>{level: <8}</level><level>{message}</level>"
logger.add(sys.stdout, colorize=True, level="INFO", format=stdout_fmt)
# Log file
logfile_fmt = "[{time:YYYY-MM-DD HH:mm:ss}] {level: <8}\t{message}"
logger.add(os.path.join(glbs.LOG_DIR, "climbr.log"), level="DEBUG", format=logfile_fmt)
# Error email handling
logger.add(error_callback, filter=lambda r: r["level"].name == "ERROR")

# Variables
data_dir = validate.directory(glbs.ES_BULK_DATA)
es_url = glbs.ES_URL if "DOCKER" not in os.environ else glbs.ES_URL_DOCKER
kibana_url = glbs.KIBANA_URL if "DOCKER" not in os.environ else glbs.KIBANA_URL_DOCKER


def get_session_yamls(path):
    """
    Gather session information from a given directory.

    :param path: path to directory containing session yamls
    :type: str
    :return: list of session files
    :rtype: list of str
    """
    if not os.path.exists(path):
        logger.error(
            f"Unable to find climbing sessions, the path '{path}' does not exist."
        )
        sys.exit(1)
    sessions = common.get_files(path, r".*\.yaml$", recursive=False)
    if not sessions:
        logger.error(
            f"Unable to find logs located at {path}. "
            "Consider using the 'demo' command to view sample data..."
        )
        sys.exit(1)
    return sessions


def log_session(args):
    """
    Create a climbing session file.

    :param args: command line arguments
    :type args: dict
    """
    filename = None
    current_time = datetime.now().strftime("%Y-%m-%d")
    default_filename = args.log_date if args.log_date else current_time
    # If the value doesn't exist or not supported, default the template
    if args.climbing_location not in glbs.GYM_TEMPLATE.keys():
        args.climbing_location = "default"
    if args.export_name:
        filename = f"{args.export_name}.yaml"
    # Special case for home gym, no need to highlight location
    elif "kanata" in args.climbing_location or "default" == args.climbing_location:
        filename = f"{default_filename}.yaml"
    else:
        filename = f"{default_filename}_{args.climbing_location}.yaml"
    climbing_log = common.copy_file(
        glbs.GYM_TEMPLATE[args.climbing_location], glbs.INPUT_DIR, filename
    )
    # Open yaml and pre-fill fields bases on config.py and cmd args
    content = common.load_yaml(climbing_log)
    if args.log_date:
        content["date"] = args.log_date
    else:
        content["date"] = datetime.now().date()
    if config.shoes and isinstance(config.shoes, str):
        content["shoes"] = config.shoes
    if config.climbers and isinstance(config.climbers, list):
        content["climbers"] = config.climbers

    common.write_yaml(content, climbing_log, force=True)
    logger.info(f"New climbing log created at '{climbing_log}'!")


def export_files(args):
    """
    Export Kibana and ES Objects to a ndjson file.

    :param args: command line arguments
    :type args: dict
    """
    # Default export name used unless overwritten
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = args.export_name if args.export_name else f"climbr_{timestamp}"
    # Default export location used unless overwritten
    destination = (
        os.path.join(args.export_dest, filename)
        if args.export_dest
        else os.path.join(glbs.OUTPUT_DIR, f"{filename}.ndjson")
    )
    common.export_kibana(kibana_url, destination)


def import_files(args):
    """
    Import Kibana and ES Objects from a ndjson file.

    :param args: command line arguments
    :type args: dict
    """
    for path in args.import_path:
        if os.path.isfile(path):
            if ".ndjson" in os.path.splitext(path)[1]:
                common.import_kibana(kibana_url, path)
            else:
                logger.error(
                    f"Unable to import '{path}'. "
                    "Invlaid file extension, must be '.ndjson'."
                )
                sys.exit(1)
        # If the given path is a directory, gather all .ndjson files
        elif os.path.isdir(path):
            files = common.get_files(path, r".*\.ndjson$")
            for file in files:
                common.import_kibana(kibana_url, file)
        else:
            logger.error(
                f"Unable to import '{path}'. File path or directory does not exist."
            )
            sys.exit(1)


def update(args, cmd):
    """
    Update Elasticsearch with latest data.

    :param args: command line arguments
    :type args: dict
    """
    # Loop through all climbing logs, normalize and add additional information
    logger.info("[1/5] Retreiving climbing logs...")
    if cmd == "demo":
        session_logs = get_session_yamls(glbs.SAMPLE_DATA_DIR)
    else:
        session_logs = get_session_yamls(glbs.INPUT_DIR)
    sessions = []
    session_data = []
    project_data = []
    counter_data = []
    project_list = {}
    logger.info("[2/5] Enhancing and normalizing data...")
    for log in session_logs:
        # Creating Session class from logs
        climbing_session = Session(log)
        # Create and maintain a running list of projects
        # Including a total counter across all Sessions
        if climbing_session.Projects:
            for project in climbing_session.Projects:
                if project.name in project_list.keys():
                    updated_total = [
                        x + y
                        for x, y in zip(
                            project_list[project.name].get_counters(),
                            project.get_counters(),
                        )
                    ]
                    # Remove is_last from the previous project instance
                    # and assign the new value to the current project
                    project_list[project.name].set_is_last(False)
                    project.set_is_last(True)
                    # Increase the running counters
                    # and update the project with the current running counter
                    project.set_total_counter(
                        updated_total[0],
                        updated_total[1],
                        updated_total[3],
                        updated_total[4],
                        updated_total[5],
                        updated_total[6],
                    )
                    # del project_list[project.name]
                    project_list[project.name] = project
                # If the project isn't in the running list, add it.
                # Total counter is default the same as counter
                else:
                    project.set_is_last(True)
                    project_list[project.name] = project
        sessions.append(climbing_session)

    # Loop through the list of Sessions and update the output lists
    for session in sessions:
        session_data.append(session.toDict())
        counter_data.extend(session.getCounters())
        project_data.extend(session.getProjects())
    logger.info("[3/5] Writing climbing data to json...")
    common.write_bulk_api(
        session_data,
        os.path.join(
            data_dir,
            "sessions.json" if cmd == "update" else "sessions_demo.json",
        ),
        "sessions",
    )
    common.write_bulk_api(
        counter_data,
        os.path.join(
            data_dir,
            "counters.json" if cmd == "update" else "counters_demo.json",
        ),
        "counters",
    )
    common.write_bulk_api(
        project_data,
        os.path.join(
            data_dir,
            "projects.json" if cmd == "update" else "projects_demo.json",
        ),
        "projects",
    )
    # Importing all data into elasticSearch
    logger.info("[4/5] Uploading data into ElasticSearch...")
    common.upload_to_es(es_url, data_dir)
    logger.info("[5/5] Visualizations and stats are ready at" f" {kibana_url}/app/home")


def init(args):
    """
    Initialize Elasticsearch and Kibana with mappings and  visualizations.

    :param args: command line arguments
    :type args: dict
    """
    # Need to wait for Kibana and ES to start up whilst using docker
    # For maintainability, writeing this here instead of bash + docker-compose
    if "DOCKER" in os.environ:
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
                    logger.error(f"Unable to ping Kibana at '{kibana_url}'")
                    sys.exit(1)
                logger.warning(
                    "ElasticSearch and Kibana services are not ready yet,"
                    " trying again in 60 seconds..."
                )
                sleep(60)
                timeout_counter += 1

    # Preparing Elasticsearch and Kibana for data consumption
    for index in glbs.ES_INDEX_NAME:
        common.create_index(
            es_url,
            index,
            validate.file(os.path.join(glbs.ES_MAPPINGS, f"{index}_mapping.json")),
            force=args.force,
        )
        common.create_index_pattern(kibana_url, index, force=args.force)
    # Importing visualizations
    common.import_kibana(
        kibana_url,
        ndjson=common.get_files(glbs.ES_DIR, "visualizations.ndjson").pop(),
    )


@logger.catch
def main():
    """Re-route command line arguments to appropriate functions."""
    args = cmd_args.init()
    cmd = args.command
    # Set system out settings
    if args.silent:
        logger.remove(1)
        logger.add(sys.stdout, colorize=True, level="ERROR", format=stdout_fmt)
    # Command-line Options
    # Initializing Kibana and ES with mappings and visualizations
    if cmd == "init":
        init(args)
    # Uploading user data into ES
    if cmd == "update" or cmd == "demo":
        update(args, cmd)
    # Exporting Kibana and ES Objects
    elif cmd == "export":
        export_files(args)
    elif cmd == "import":
        import_files(args)
    elif cmd == "log":
        log_session(args)


if __name__ == "__main__":
    main()
