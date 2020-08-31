
#!/usr/bin/python3
'''
This module contains classes and functions that relate to climbing sessions and it's data manipulation
'''
import datetime
import common.constants as constants
import common.common as common
import common.validate as validate
# Classes


class Location:
    '''
    A location object that contains basic information about a climbing location
    :param name: The name of the location
    :param address: Full address of the location
    :param lat: Latitude
    :param lon: Longitude
    :param grading: A list of the grading scale used
    :param is_outdoor: The style of climbing, indoor/ outdoor
    :type name: str
    :type address: str
    :type lat: float
    :type lon: float
    :type grading: list
    :type is_outdoor: bool
    '''

    def __init__(self, name, address, lat, lon, grading, is_outdoor):
        try:
            self.name = name
            self.address = address
            self.lat = lat
            self.lon = lon
            self.grading = grading
            self.is_outdoor = is_outdoor
        except Exception as ex:
            raise ex


class Session:
    '''
    A climbing session object that contains information from user logs
    :param session_log: A dict containing information on a climbing session
    :type: dict
    '''

    def __init__(self, session_log):
        try:
            # Validate, normalize and add additional information to session log data
            validated = is_valid(common.load_yaml(session_log))
            normalized = normalize(validated)
            session_info = enchance(normalized)
            # Class variables
            self.climbers = session_info['climbers']
            self.coordinates = session_info['coordinates']
            self.date = session_info['date']
            self.description = session_info['description']
            self.duration = session_info['duration']
            self.end_time = session_info['time']['end']
            self.injury = session_info['injury']
            self.location_name = session_info['location']
            self.media = session_info['media']
            self.projects = session_info['projects']
            self.session_counter = session_info['session_counter']
            self.shoes = session_info['shoes'] if 'shoes' in session_info.keys(
            ) else None
            self.start_time = session_info['time']['start']
            self.style = session_info['style']
            # Location class
            self.Location = get_location(session_info['location'])
        except Exception as ex:
            raise ex

    def toDict(self):
        '''
        Return the object as a dictionary
        :return: Session dictionary
        :rtype: dict
        '''
        try:
            return {
                "location": self.location_name,
                "coordinates": self.coordinates,
                "style": self.style,
                "date": self.date,
                "description": self.description,
                "start": self.start_time,
                "end": self.end_time,
                "climbers": self.climbers,
                "injury": self.injury,
                "session_counter": self.session_counter,
                "projects": self.projects,
                "media": self.media,
                "shoes": self.shoes,
                "duration": self.duration
            }
        except Exception as ex:
            raise ex


# Variables
_ALTITUDE_SCALE = ['VB/V0', 'V0/V1', 'V1/V2', 'V2/V3', 'V3/V4', 'V4/V5', 'V5/V6', 'V6/V7', 'V7/V8', 'V8/V9', 'V9+',
                   'Kids - VB/V0', 'Kids - V0/V1', 'Kids - V1/V2', 'Kids - V2/V3', 'Kids - V3/V4', 'Kids - V4/V5',
                   'Kids - V5/V6', 'Kids - V6/V7', 'Kids - V7/V8', 'Kids - V8/V9', 'Kids - V9+', 'competition', 'routesetting-squad']
_LOCATIONS = [Location('Altitude Kanata', '0E5, 501 Palladium Dr, Kanata, ON K2V 0E5', 45.297970, -75.911150, _ALTITUDE_SCALE, False),
              Location('Altitude Gatineau', '35 Boulevard Saint-Raymond, Gatineau, QC J8Y 1R5', 45.446861, -
                       75.736801, _ALTITUDE_SCALE, False),
              Location("Hog's Back Falls", 'Hog\'s Back Falls, Ottawa, ON', 45.3710517, -
                       75.698022, constants.V_SCALE, True),
              Location("Calabogie", 'Greater Madawaska, Ontario', 45.264209, -
                       76.813545, constants.V_SCALE, True),
              Location('Lac Beauchamp', 'Lac Beauchamp, Gatineau, QC', 45.490288, -
                       75.617274, constants.V_SCALE, True),
              Location('Coyote Rock Gym', '1737B St Laurent Blvd, Ottawa, ON K1G 3V4', 45.406130, -75.625500, ['White', 'Orange', 'Red',
                                                                                                               'Blue', 'Green', 'Purple', 'Black', 'Ungraded'], False)]

# Functions


def enchance(session_log):
    '''
    Add coordinates, climbing duration and other information to session data
    :param session_log: climbing session object
    :type session_log: dict
    :return: enhanced session log with duration, lon, lat values added
    :rtype: dict
    '''
    try:
        # Get/set climbing duration
        duration = common.str_to_time(
            session_log['time']['end']) - common.str_to_time(session_log['time']['start'])
        session_log['duration'] = str(duration)
        # Get/set lon and latitude
        location = get_location(session_log['location'])
        session_log['coordinates'] = [location.lon, location.lat]
        return session_log
    except Exception as ex:
        raise ex


def get_location(name):
    '''
    Returns location object based on a name parameter. If no location is found, will return None
    :param name: name of location
    :type name: str
    :return: location information
    :rtype: Location or None
    '''
    try:
        for location in _LOCATIONS:
            if name == location.name:
                return location
        return None
    except Exception as ex:
        raise ex


def get_location_names():
    '''
    Retrieves a list of location names
    :return: location names
    :rtype: list
    '''
    try:
        location_names = []
        for location in _LOCATIONS:
            location_names.append(location.name)
        return location_names
    except Exception as ex:
        raise ex


def is_valid(session_log):
    '''
    Validating if a session_log has all minimal required fields. Returning the session object if valid
    :param session_log: a session_log that contains a dict of session information and stats
    :type session_log: dict
    :raises Exception: Climbing session does not meet minimal required fields
    :return: session
    :rtype: dict
    '''
    try:
        # Required fields
        session_keys = session_log.keys()
        required = {'location': 'location' in session_keys,
                    'style': 'style' in session_keys,
                    'date': 'date' in session_keys,
                    'time': 'time' in session_keys,
                    'start_time': 'time' in session_keys and 'start' in session_log['time'].keys(),
                    'end_time': 'time' in session_keys and 'end' in session_log['time'].keys(),
                    'session_counter': 'session_counter' in session_keys}
        missing = []
        # If not all values are present, then raise an error
        if not (all(list(required.values()))):
            for item in required:
                if not required[item]:
                    missing.append(item)
            raise Exception(f"Unable to find required values: {missing}")

        # Basic field type validation
        valid_location = type(session_log['location']) == str
        valid_style = type(session_log['style']) == str
        valid_description = type(
            session_log['description']) == str if 'description' in session_keys else True
        valid_date = True
        if type(session_log['date']) == datetime.date:
            try:
                validate.date(str(session_log['date']))
            except Exception as ex:
                valid_date = False
        else:
            valid_date = False
        valid_time = type(session_log['time']) == dict
        valid_start_time = type(session_log['time']['start']) == str
        valid_end_time = type(session_log['time']['end']) == str
        # Validating climbers field if it exists, and it's children fields
        valid_climbers = True
        if 'climbers' in session_keys and type(session_log['climbers']) == list:
            for climber in session_log['climbers']:
                if type(climber) != str:
                    valid_climbers = False
                    break
        else:
            valid_climbers = False
        valid_climbers = type(
            session_log['climbers']) == list if 'climbers' in session_keys else True
        valid_injury = True
        if 'injury' in session_keys:
            if type(session_log['injury']) == dict and set(['isTrue', 'description']).issubset(session_log['injury'].keys()):
                if type(session_log['injury']['isTrue']) != bool or type(session_log['injury']['description']) != str:
                    valid_injury = False
            else:
                valid_injury = False
        valid_media = True
        if 'media' in session_keys:
            if type(session_log['media']) == list:
                for item in session_log['media']:
                    if type(item) != str:
                        valid_media = False
                        break
            elif type(session_log['media']) is type(None):
                pass
            else:
                valid_media = False
        valid_session_counter = type(session_log['session_counter']) == list
        if valid_session_counter:
            for counter in session_log['session_counter']:
                min_set = ['grade', 'flash', 'redpoint', 'repeat', 'attempts']
                if 'outdoor' in session_log['style']:
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
        valid_projects = True
        if 'projects' in session_keys:
            if type(session_log['projects']) == list:
                for climb in session_log['projects']:
                    min_set = ['name', 'location', 'style', 'grade',
                               'flash', 'redpoint', 'repeat', 'attempts']
                    if 'outdoor' in session_log['style']:
                        min_set.append('onsight')
                    if set(min_set).issubset(list(climb.keys())):
                        climb_fields = [type(climb['name']) == str,
                                        type(climb['location']) == str,
                                        type(climb['style']) == list,
                                        type(climb['grade']) == str,
                                        type(climb['flash']) == int and climb['flash'] in [
                                            0, 1],
                                        type(climb['redpoint']) == int and climb['redpoint'] in [
                                            0, 1],
                                        type(climb['repeat']
                                             ) == int and climb['repeat'] >= 0,
                                        type(climb['attempts']) == int and climb['attempts'] >= 0]
                        # For projects, Flash, Redpoint and Onsighting are mutually exclusive
                        if (climb['flash'] and climb['redpoint']):
                            climb_fields.append(False)
                        if 'onsight' in climb.keys():
                            climb_fields.extend(
                                [type(climb['onsight']) == int and climb['onsight'] in [0, 1],
                                 not (climb['flash'] and climb['onsight']),
                                 not (climb['redpoint'] and climb['onsight'])])
                        if not all(climb_fields):
                            valid_projects = False
                            break
                    else:
                        valid_projects = False
                        break
            else:
                valid_projects = False
        valid_shoes = type(
            session_log['shoes']) == str if 'shoes' in session_keys else True
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
                        'projects': valid_projects,
                        'shoes': valid_shoes}
        # If all fields are not valid, then raise an error with the offending fields
        if not (all(list(valid_fields.values()))):
            for field in valid_fields:
                if not valid_fields[field]:
                    missing.append(field)
            raise Exception(
                f"Invalid syntax for the following fields: {missing}")
        # If passes all validation, then just return the value
        return session_log
    except Exception as ex:
        raise ex


def normalize(session_log):
    '''
    Normalize and fill missing fields in a session log
    :param session_log: climbing session object
    :type session_log: dict
    :return: normalized session object
    :rtype: dict
    '''
    try:
        available_fields = session_log.keys()
        location = get_location(session_log['location'])

        if not location:
            raise Exception(
                f"No location found for {session_log['location']}. Current supported locations include: {get_location_names()}")
        # Split the style field by commas and turn it into a list instead
        #  This is because style could be multiple fields ie. indoor bouldering, indoor lead
        session_log['style'] = session_log['style'].split(',')
        # Compare the session_counter list with the location's grading scale
        # If any counters are missing, add to it and just defult to 0 for all categories
        counted_grades = []
        for counter in session_log['session_counter']:
            counted_grades.append(counter['grade'])
        missing_counters = list(set(location.grading) - set(counted_grades))
        for counter in missing_counters:
            default_counter = {'grade': counter, 'flash': 0,
                               'redpoint': 0, 'repeat': 0, 'attempts': 0}
            if location.is_outdoor:
                default_counter['onsight'] = 0
            session_log['session_counter'].append(default_counter)
        session_log['session_counter'] = reformat_counter(
            session_log['session_counter'])
        # Look at the optional fields and add filler values
        if 'climbers' not in available_fields:
            session_log['climbers'] = None
        if 'injury' not in available_fields:
            session_log['injury'] = {'isTrue': False, 'description': None}
        elif session_log['injury']['isTrue'] == False and session_log['injury']['description'] == 'Add a description of injury here':
            session_log['injury'] = {'isTrue': False, 'description': None}
        if 'media' not in available_fields:
            session_log['media'] = None
        if 'projects' not in available_fields:
            session_log['projects'] = None
        else:
            for climb in session_log['projects']:
                if 'notes' not in climb.keys():
                    climb['notes'] = None
                if 'media' not in climb.keys():
                    climb['media'] = None
        session_log['projects'] = reformat_projects(session_log['projects'])
        # Format all time
        session_log['time']['start'] = common.convert_to_hhmm(
            session_log['time']['start'])
        session_log['time']['end'] = common.convert_to_hhmm(
            session_log['time']['end'])
        # Reformat date
        session_log['date'] = str(session_log['date'])
        return session_log
    except Exception as ex:
        raise ex


def reformat_counter(counters):
    '''
    Restructuring the list session_counter to nest onsight,flash,redpoint,repeat and attempts under the grade name.
    :param counters: list of sessions logs
    :type: list of dict
    :return: reformatted list of sessions logs
    :rtype: list of dict
    '''
    try:
        reformatted = []
        for counter in counters:
            new_counter = {counter['grade']: {"flash": counter['flash'],
                                              "redpoint": counter['redpoint'],
                                              "repeat": counter['repeat'],
                                              "attempts": counter['attempts']}}
            if 'onsight' in counter.keys():
                new_counter[counter['grade']]['onsight'] = counter['onsight']
            reformatted.append(new_counter)
        return reformatted
    except Exception as ex:
        raise ex


def reformat_projects(projects):
    '''
    Restructuring the list projects to nest project details under the project name.
    :param projects: list of projects
    :type: list of dict
    :return: reformatted list of projects
    :rtype: list of dict
    '''
    try:
        reformatted = []
        # Return nothing if the list of projects is empty
        if not projects:
            return projects
        # Otherwise loop through and reformat
        for project in projects:
            new_project = {project['name']: {"location": project['location'],
                                             "style": project['style'],
                                             "grade": project['grade'],
                                             "flash": project['flash'],
                                             "redpoint": project['redpoint'],
                                             "repeat": project['repeat'],
                                             "attempts": project['attempts'],
                                             "notes": project['notes'],
                                             "media": project['media']}}
            if 'onsight' in project.keys():
                new_project[project['name']]['onsight'] = project['onsight']
            reformatted.append(new_project)
        return reformatted
    except Exception as ex:
        raise ex
