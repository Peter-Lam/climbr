#!/usr/bin/python
'''File containing validation utilities'''

import datetime
import socket
import os
import yaml
import common.common as common


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


def session(session):
    '''
    Validating if a climbing session has all minimal required fields. Returning the session object if valid
    :param sessions: Climbing session object
    :type session: dict
    :raises Exception: Climbing session does not meet minimal required fields
    :return: session
    :rtype: dict
    '''
    # Required fields
    session_keys = session.keys()
    required = {'location': 'location' in session_keys,
                'style': 'style' in session_keys,
                'date': 'date' in session_keys,
                'time': 'time' in session_keys,
                'start_time': 'time' in session_keys and 'start' in session['time'].keys(),
                'end_time': 'time' in session_keys and 'end' in session['time'].keys(),
                'session_counter': 'session_counter' in session_keys}
    missing = []
    # If not all values are present, then raise an error
    if not (all(list(required.values()))):
        for item in required:
            if not required[item]:
                missing.append(item)
        raise Exception(f"Unable to find required values: {missing}")

    # Basic field type validation
    valid_location = type(session['location']) == str
    valid_style = type(session['style']) == str
    valid_description = type(
        session['description']) == str if 'description' in session_keys else True
    valid_date = True
    if type(session['date']) == datetime.date:
        try:
            date(str(session['date']))
        except Exception as ex:
            valid_date = False
    else:
        valid_date = False
    valid_time = type(session['time']) == dict
    valid_start_time = type(session['time']['start']) == str
    valid_end_time = type(session['time']['end']) == str
    # Validating climbers field if it exists, and it's children fields
    valid_climbers = True
    if 'climbers' in session_keys and type(session['climbers']) == list:
        for climber in session['climbers']:
            if type(climber) != str:
                valid_climbers = False
                break
    else:
        valid_climbers = False
    valid_climbers = type(
        session['climbers']) == list if 'climbers' in session_keys else True
    valid_injury = True
    if 'injury' in session_keys:
        if type(session['injury']) == dict and set(['isTrue', 'description']).issubset(session['injury'].keys()):
            if type(session['injury']['isTrue']) != bool or type(session['injury']['description']) != str:
                valid_injury = False
        else:
            valid_injury = False
    valid_media = True
    if 'media' in session_keys:
        if type(session['media']) == list:
            for item in session['media']:
                if type(item) != str:
                    valid_media = False
                    break
        elif type(session['media']) is type(None):
            pass
        else:
            valid_media = False
    valid_session_counter = type(session['session_counter']) == list
    if valid_session_counter:
        for counter in session['session_counter']:
            min_set = ['grade', 'flash', 'redpoint', 'repeat', 'attempts']
            if 'outdoor' in session['style']:
                min_set.append('onsight')
            if set(min_set).issubset(counter.keys()):
                for item in min_set:
                    if item == 'grade' and type(counter[item]) != str:
                        valid_session_counter = False
                        break
                    elif item != 'grade' and type(counter[item]) != int:
                        valid_session_counter = False
                        break
            else:
                valid_session_counter = False
                break
    valid_climbs = True
    if 'climbs' in session_keys:
        if type(session['climbs']) == list:
            for climb in session['climbs']:
                min_set = ['name', 'location', 'style', 'grade',
                           'flash', 'redpoint', 'repeat', 'attempts']
                if 'outdoor' in session['style']:
                    min_set.append('onsight')
                if set(min_set).issubset(list(climb.keys())):
                    climb_fields = []
                    climb_fields.append(type(climb['name']) == str)
                    climb_fields.append(type(climb['location']) == str)
                    climb_fields.append(type(climb['style']) == list)
                    climb_fields.append(type(climb['grade']) == str)
                    climb_fields.append(
                        type(climb['flash']) == int and climb['flash'] in [0, 1])
                    climb_fields.append(
                        type(climb['redpoint']) == int and climb['redpoint'] in [0, 1])
                    climb_fields.append(
                        type(climb['repeat']) == int and climb['repeat'] >= 0)
                    climb_fields.append(
                        type(climb['attempts']) == int and climb['attempts'] >= 0)
                    if 'onsight' in climb.keys():
                        climb_fields.append(
                            type(climb['onsight']) == int and climb['onsight'] in [0, 1])
                    if not all(climb_fields):
                        valid_climbs = False
                        break
                else:
                    valid_climbs = False
                    break
        else:
            valid_climbs = False

    valid_climbs_fields = None
    valid_shoes = type(
        session['shoes']) == str if 'shoes' in session_keys else True

    valid_fields = {'location': valid_location,
                    'style': valid_style,
                    'description': valid_description,
                    'date': valid_date,
                    'time': valid_time,
                    'start': valid_start_time,
                    'end': valid_end_time,
                    'climbers': valid_climbers,
                    'injury': valid_injury,
                    'media': valid_media,
                    'session_counter': valid_session_counter,
                    'climbs': valid_climbs,
                    'shoes': valid_shoes}
    # If all fields are not valid, then raise an error with the offending fields
    if not (all(list(valid_fields.values()))):
        for field in valid_fields:
            if not valid_fields[field]:
                missing.append(field)
        raise Exception(f"Invalid syntax for the following fields: {missing}")
    # If passes all validation, then just return the value
    return session
