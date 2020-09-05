
#!/usr/bin/python3
'''
This module contains classes and functions that relate to climbing sessions and it's data manipulation
'''
import datetime
import common.constants as constants
import common.common as common
import common.validate as validate
# Classes


class Counter:
    '''
    A counter that tracks a specific grade's stats: Onsight, Flash, Redpoint, Repeat, Attempts
    :param grade: The grade of the problem (ie V4/V5)
    :param flash: Number of flashes
    :param redpoint: Number of redpoints
    :param attempts: Number of attempts
    :param onsight: Optional - Number of onsight
    :type grade: int
    :type flash: int
    :type redpoint: int
    :type attempts: int
    :type onsight: int
    '''

    def __init__(self, grade, flash, redpoint, repeat, attempts, onsight=None):
        try:
            # TO DO: Move validation of counters here
            self.grade = grade
            self.onsight = onsight
            self.flash = flash
            self.redpoint = redpoint
            self.repeat = repeat
            self.attempts = attempts
            self.completed = int(self.onsight or 0) + \
                self.flash + self.redpoint + self.repeat
            self.total = self.completed + attempts
        except Exception as ex:
            raise ex

    def toDict(self):
        '''
        Return the object as a dictionary
        :return: Problem dictionary
        :rtype: dict
        '''
        try:
            counter_dict = {"grade": self.grade,
                            "flash": self.flash,
                            "redpoint": self.redpoint,
                            "repeat": self.repeat,
                            "attempts": self.attempts,
                            "completed": self.completed,
                            "total": self.total
                            }
            if self.onsight:
                counter_dict['onsight'] = self.onsight
            return counter_dict
        except Exception as ex:
            raise ex


class Project(Counter):
    '''
    A specifc problem/route that is being worked on for many sessions. Identified by the 'name', a Project
    is a subclass of Counter with the addition of fields such as style, media, notes, location
    :param name: The identifying name of the project
    :param location: The location of the problem (ie. Quarry)
    :param style: The style of problem (ie. Dyno)
    :param notes: Any notes from the climbing session about the project
    :param media: Photos and videos of the project
    :type name: str
    :type location: str
    :type style: str
    :type notes: str
    :type media: list of str
    '''

    def __init__(self, grade, flash, redpoint, repeat, attempts, name, location, style, notes, media, onsight=None):
        try:
            # TO DO: Move validation of projects here
            self.name = name
            self.location = location
            self.style = style
            self.notes = notes
            self.media = media
            super().__init__(grade, flash, redpoint, repeat, attempts, onsight)
        except Exception as ex:
            raise ex

    def toDict(self):
        '''
        Return the object as a dictionary
        :return: Problem dictionary
        :rtype: dict
        '''
        try:
            project_dict = {"name": self.name,
                            "location": self.location,
                            "style": self.style,
                            "grade": self.grade,
                            "flash": self.flash,
                            "redpoint": self.redpoint,
                            "repeat": self.repeat,
                            "attempts": self.attempts,
                            "completed": self.completed,
                            "total": self.total,
                            "notes": self.notes,
                            "media": self.media
                            }
            if self.onsight:
                project_dict['onsight'] = self.onsight
            return project_dict
        except Exception as ex:
            raise ex


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
    :param session_log: A YAML path containing information on a climbing session
    :type: str
    '''

    def __init__(self, session_log):
        try:
            # Validate, normalize and add additional information to session log data
            validated = self.__is_valid(common.load_yaml(session_log))
            normalized = self.__normalize(validated)
            session_info = self.__enchance(normalized)
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
            self.shoes = session_info['shoes'] if 'shoes' in session_info.keys(
            ) else None
            self.start_time = session_info['time']['start']
            self.style = session_info['style']
            # Classes
            self.Location = get_location(session_info['location'])
            self.Projects = session_info['projects']  # List of Projects
            self.Counters = session_info['counter']  # List of Counters
            # Total Counters
            self.flash = session_info['flash']
            self.redpoint = session_info['redpoint']
            self.repeat = session_info['repeat']
            self.attempts = session_info['attempts']
            self.completed = session_info['completed']
            self.total_problems = session_info['total_problems']
            if self.Location.is_outdoor:
                self.onsight = session_info['onsight']
            # If the session location is at Altitude Kanata, then track kids VS adult problems
            if self.Location.lat == 45.297970 and self.Location.lon == -75.911150:
                self.flash_kids = session_info['flash_kids']
                self.redpoint_kids = session_info['redpoint_kids']
                self.repeat_kids = session_info['repeat_kids']
                self.attempts_kids = session_info['attempts_kids']
                self.completed_kids = session_info['completed_kids']
                self.total_problems_kids = session_info['total_problems_kids']

                self.flash_adult = session_info['flash_adult']
                self.redpoint_adult = session_info['redpoint_adult']
                self.repeat_adult = session_info['repeat_adult']
                self.attempts_adult = session_info['attempts_adult']
                self.completed_adult = session_info['completed_adult']
                self.total_problems_adult = session_info['total_problems_adult']
                if self.Location.is_outdoor:
                    self.onsight_kids = session_info['onsight_kids']
                    self.onsight_adult = session_info['onsight_adult']
        except Exception as ex:
            raise ex

    def __is_valid(self, session_log):
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
                        'counter': 'counter' in session_keys}
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
            valid_counter = type(session_log['counter']) == list
            if valid_counter:
                for counter in session_log['counter']:
                    min_set = ['grade', 'flash',
                               'redpoint', 'repeat', 'attempts']
                    if 'outdoor' in session_log['style']:
                        min_set.append('onsight')
                    if set(min_set).issubset(counter.keys()):
                        for item in min_set:
                            if item == 'grade' and type(counter[item]) != str:
                                valid_counter = False
                                break
                            elif item != 'grade' and type(counter[item]) != int:
                                valid_counter = False
                                break
                    else:
                        valid_counter = False
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
                            'counter': valid_counter,
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

    def __normalize(self, session_log):
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
            # Compare the counter list with the location's grading scale
            # If any counters are missing, add to it and just defult to 0 for all categories
            counted_grades = []
            for counter in session_log['counter']:
                counted_grades.append(counter['grade'])
            missing_counters = list(
                set(location.grading) - set(counted_grades))
            for counter in missing_counters:
                default_counter = {'grade': counter, 'flash': 0,
                                   'redpoint': 0, 'repeat': 0, 'attempts': 0}
                if location.is_outdoor:
                    default_counter['onsight'] = 0
                session_log['counter'].append(default_counter)
            session_log['counter'] = reformat_counter(
                session_log['counter'])
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
            session_log['projects'] = reformat_projects(
                session_log['projects'])
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

    def __enchance(self, session_log):
        '''
        Adding coordinates, climbing duration and other information for data analysis
        :param session_log: climbing session object
        :type session_log: dict
        :return: enhanced session log with duration, lon, lat values, and additional counters added
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
            # Boolean variable to add extra stats for Altitude Kanata
            altitude_kanata = location.lat == 45.297970 and location.lon == -75.911150
            # Iterate through counters and create total counter
            for name in ['onsight', 'flash', 'redpoint', 'repeat', 'attempts', 'completed', 'total_problems']:
                session_log.update({name: 0})
                if altitude_kanata:
                    session_log.update({name + '_kids': 0})
                    session_log.update({name + '_adult': 0})
            for counter_obj in session_log['counter']:
                session_log['onsight'] += counter_obj.onsight if counter_obj.onsight else 0
                session_log['flash'] += counter_obj.flash
                session_log['redpoint'] += counter_obj.redpoint
                session_log['repeat'] += counter_obj.repeat
                session_log['attempts'] += counter_obj.attempts
                session_log['completed'] += counter_obj.completed
                session_log['total_problems'] += counter_obj.total
                # Add more fields if it's
                if altitude_kanata:

                    if 'Kids' in counter_obj.grade:
                        session_log['onsight_kids'] += counter_obj.onsight if counter_obj.onsight else 0
                        session_log['flash_kids'] += counter_obj.flash
                        session_log['redpoint_kids'] += counter_obj.redpoint
                        session_log['repeat_kids'] += counter_obj.repeat
                        session_log['attempts_kids'] += counter_obj.attempts
                        session_log['completed_kids'] += counter_obj.completed
                        session_log['total_problems_kids'] += counter_obj.total
                    else:
                        session_log['onsight_adult'] += counter_obj.onsight if counter_obj.onsight else 0
                        session_log['flash_adult'] += counter_obj.flash
                        session_log['redpoint_adult'] += counter_obj.redpoint
                        session_log['repeat_adult'] += counter_obj.repeat
                        session_log['attempts_adult'] += counter_obj.attempts
                        session_log['completed_adult'] += counter_obj.completed
                        session_log['total_problems_adult'] += counter_obj.total
            return session_log
        except Exception as ex:
            raise ex

    def toDict(self):
        '''
        Return the object as a dictionary
        :return: Session dictionary
        :rtype: dict
        '''
        try:
            session_dict = {
                "location": self.location_name,
                "coordinates": self.coordinates,
                "style": self.style,
                "date": self.date,
                "description": self.description,
                "start": self.start_time,
                "end": self.end_time,
                "climbers": self.climbers,
                "injury": self.injury,
                "media": self.media,
                "shoes": self.shoes,
                "duration": self.duration,
                "flash": self.flash,
                "redpoint": self.redpoint,
                "repeat": self.repeat,
                "attempts": self.attempts,
                "completed": self.completed,
                "total_problems": self.total_problems
            }
            if self.Location.is_outdoor:
                session_dict['onsight'] = self.onsight
            if self.Location.lat == 45.297970 and self.Location.lon == -75.911150:
                session_dict['flash_kids'] = self.flash_kids
                session_dict['redpoint_kids'] = self.redpoint_kids
                session_dict['repeat_kids'] = self.repeat_kids
                session_dict['attempts_kids'] = self.attempts_kids
                session_dict['completed_kids'] = self.completed_kids
                session_dict['total_problems_kids'] = self.total_problems_kids

                session_dict['flash_adult'] = self.flash_adult
                session_dict['redpoint_adult'] = self.redpoint_adult
                session_dict['repeat_adult'] = self.repeat_adult
                session_dict['attempts_adult'] = self.attempts_adult
                session_dict['completed_adult'] = self.completed_adult
                session_dict['total_problems_adult'] = self.total_problems_adult
                if self.Location.is_outdoor:
                    session_dict['onsight_kids'] = self.onsight_kids
                    session_dict['onsight_adult'] = self.onsight_adult
            return session_dict
        except Exception as ex:
            raise ex

    def getProjects(self):
        '''
        Return the projects as a dictionary
        :return: Project dictionary
        :rtype: dict
        '''
        try:
            projects = []
            if self.Projects:
                for project in self.Projects:
                    project_dict = project.toDict()
                    project_dict.update({"session": {"location": self.location_name,
                                                     "style": self.style,
                                                     "date": self.date,
                                                     "shoes": self.shoes}})
                    projects.append(project_dict)
            return projects
        except Exception as ex:
            raise ex

    def getCounters(self):
        '''
        Return the climbing counters as a dictionary with additional session information
        :return: Counter dictionary
        :rtype: list of dict
        '''
        try:
            counters = []
            for session_counter in self.Counters:
                counter_dict = session_counter.toDict()
                counter_dict.update({"session": {"location": self.location_name,
                                                 "style": self.style,
                                                 "date": self.date,
                                                 "shoes": self.shoes}})
                counters.append(counter_dict)
            return counters
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


def reformat_counter(counters):
    '''
    Converting the list of counters dicts to objects
    :param counters: list of counter logs
    :type: list of dict
    :return: Converted dicts to Counters
    :rtype: list of Counter
    '''
    try:
        reformatted = []
        for counter in counters:
            if 'onsight' in counter.keys():
                reformatted.append(Counter(counter['grade'], counter['flash'],
                                           counter['redpoint'], counter['attempts'], counter['repeat'], onsight=counter['onsight']))
            else:
                reformatted.append(Counter(
                    counter['grade'], counter['flash'], counter['redpoint'], counter['repeat'], counter['attempts']))
        return reformatted
    except Exception as ex:
        raise ex


def reformat_projects(projects):
    '''
    Converting the list of projects dicts to objects
    :param projects: list of projects
    :type: list of dict
    :return: Coverted dicts to Projects
    :rtype: list of Project
    '''
    try:
        reformatted = []
        # Return nothing if the list of projects is empty
        if not projects:
            return projects
        # Otherwise loop through and reformat
        for project in projects:
            if 'onsight' in project.keys():
                reformatted.append(Project(project['grade'], project['flash'], project['redpoint'],
                                           project['repeat'], project['attempts'], project['name'],
                                           project['location'], project['style'], project['notes'],
                                           project['media'], onsight=project['onsight']))
            else:
                reformatted.append(Project(project['grade'], project['flash'], project['redpoint'],
                                           project['repeat'], project['attempts'], project['name'],
                                           project['location'], project['style'], project['notes'],
                                           project['media']))
        return reformatted
    except Exception as ex:
        raise ex