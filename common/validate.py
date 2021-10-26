#!/usr/bin/python
"""File containing validation utilities."""

import datetime
import os
import re


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
            raise TypeError("Excepting string parameter, but got {type(value)} instead")
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        raise ValueError(
            f"Inappropriate data format for '{value}', expecting YYYY-MM-DD"
        )
    except Exception as ex:
        raise ex


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
        raise IOError(f"'{path}' is not a directory.")
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
        raise Exception(f"Invalid email:'{value}'")
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
        raise IOError(f"'{path}' is not a file.")
    return path
