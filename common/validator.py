#!/usr/bin/python
'''File containing validation utilities'''

import datetime
import socket


def is_valid_date(value, raise_error=False):
    '''
    Validating if date string is in DD/MM/YYYY format
    If raise_error is enabled then raise an error, otherwise return false
    :param value: value to validate
    :param raise_error: option for error handling
    :type value: string
    :type raise_error: boolean
    :return: returns the result of validation check
    :rtype: boolean
    '''
    try:
        datetime.datetime.strptime(value, '%m/%d/%Y')
        return True
    except ValueError as message:
        if raise_error:
            raise Exception(message)
        return False
    return False


def is_valid_kibana_config(config, raise_error=False):
    '''
    Validating if a given config object is valid for Kibana
    If raise_error is enabled then raise an error, otherwise return false
    :param config: config to validate
    :param raise_error: option for error handling
    :type config: dict
    :type raise_error: boolean
    :return: returns the result of validation check
    :rtype: boolean
    '''
    required_fields = ['api_key', 'ip_api', 'api_limit']
    for field in required_fields:
        if field not in config.keys():
            if raise_error:
                raise Exception(
                    f"Error - The field '{field}' must be present in the config file")
            return False
    if len(config['api_key']) == 0:
        if raise_error:
            raise Exception(
                f"Error - The field 'api_key' must have at least 1 key")
        return False
    if not config['ip_api']:
        if raise_error:
            raise Exception(f"Error - Missing API key for ip_api")
        return False
    if not config['api_limit'] > 0:
        if raise_error:
            raise Exception(f"Error - api limit must be greater than 0")
        return False
    return True
