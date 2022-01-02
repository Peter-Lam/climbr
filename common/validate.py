#!/usr/bin/python
"""File containing validation utilities."""

import datetime
import os
import re
import sys

from loguru import logger


def date(value):
    """
    Check if date string is in YYYY-MM-DD format.

    Returns value if true, otherwise raises error.

    :param value: date to validate
    :type value: string
    :raises Exception: Date does not follow YYYY-MM-DD format
    :return: returns date string
    :rtype: string
    """
    try:
        if type(value) != str:
            logger.error("Excepting string parameter, but got {type(value)} instead")
            sys.exit(1)
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        logger.error(f"Inappropriate data format for '{value}', expecting YYYY-MM-DD")
        sys.exit(1)


def directory(path):
    """
    Check if path is a directory. Returns value if true, otherwise raises error.

    :param path: Path to directory
    :type path: str
    :raises Exception: directory does not exist
    :return: path
    :rtype: str
    """
    if not os.path.isdir(path):
        logger.error(f"'{path}' is not a directory.")
        sys.exit(1)
    return path


def email(value):
    """
    Check if value is a valid email based on regex.

    Returns value if true otherwise raises error.

    :param value: email to verify
    :type value: str
    :return: email
    :rtype: str
    :raises Exception: email does not exist
    """
    regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$"
    if not re.search(regex, value):
        logger.error(f"Invalid email:'{value}'")
        sys.exit(1)
    return value


def file(path):
    """
    Check if path is a file. Returns value if true otherwise raises error.

    :param path: Path to file
    :type path: str
    :raises Exception: file path does not exist
    :return: path
    :rtype: str
    """
    if not os.path.isfile(path):
        logger.error(f"'{path}' is not a file.")
        sys.exit(1)
    return path
