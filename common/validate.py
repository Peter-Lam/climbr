#!/usr/bin/python
'''File containing validation utilities'''

import datetime
import socket
import os
import yaml


def date(value):
    '''
    Validating if date string is in YYYY-MM-DD format. Returning the value if true, otherwise raises an error
    :param value: date to validate
    :type value: string
    :raises Exception: Date does not follow YYYY-MM-DD format
    :return: returns date string
    :rtype: string
    '''
    try:
        if type(value) != str:
            raise TypeError(
                "Excepting string parameter, but got {type(value)} instead")
        datetime.datetime.strptime(value, '%Y-%m-%d')
        return value
    except ValueError as message:
        raise ValueError(
            f"Inappropriate data format for '{value}', expecting YYYY-MM-DD")
    except Exception as ex:
        raise ex


def directory(path):
    '''
    Checking if path is a directory, raises error otherwise
    :param path: Path to directory
    :type path: str
    :raises Exception: directory does not exist
    :return: path
    :rtype: str
    '''
    if not os.path.isdir(path):
        raise IOError(f"'{path}' is not a directory.")
    return path


def file(path):
    '''
    Checking if path is a file, raises error otherwise
    :param path: Path to file
    :type path: str
    :raises Exception: file path does not exist
    :return: path
    :rtype: str
    '''
    if not os.path.isfile(path):
        raise IOError(f"'{path}' is not a file.")
    return path
