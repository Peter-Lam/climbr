#!/usr/bin/python3

# --------------------------------
# USe this script to periodically update weather data to bookings.json
# --------------------------------

import os
import json
import requests
import sys
import pandas as pd
import datetime
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
import common.globals as glbs  # noqa
import common.common as common  # noqa
import config as config  # noqa


def last_updated(city):
    '''
    Get the date for the last CSV entry of weather info as a datetime object
    :param city: The city to get weather data from
    :type city: str
    :return: date of the last entry
    :rtype: datetime
    '''
    try:
        init = None
        if city in ['Ottawa', 'Gatineau']:
            if city == 'Ottawa':
                init = pd.read_csv(glbs.OTTAWA_WEATHER)
            elif city == 'Gatineau':
                init = pd.read_csv(glbs.GATINEAU_WEATHER)
            init['Date time'] = pd.to_datetime(init['Date time'])
            datetime = init.iloc[-1]['Date time']
        else:
            raise Exception(
                "That location is currently not supported. Try 'Ottawa' or 'Gatineau'")
        return datetime
    except Exception as ex:
        raise ex


def get_bookings():
    '''
    Retreive booking data and return the data
    '''
    try:
        file = os.path.join(glbs.ES_BULK_DATA, 'bookings.json')
        return common.load_bulk_json(file)
    except Exception as ex:
        raise ex


def get_weather(city, last_updated):
    '''
    Use visualcrossing api to get historical weather by params up until the day before the current date. Returning a pandas dataframe
    :param city: city for weather data
    :param last_updated: the last weather entry that is stored locally
    :type city: str
    :type last_updated: datetime
    :return: Historical weather data
    :rtype: dataframe
    '''
    try:
        last_updated += datetime.timedelta(days=1)
        start_date = str(last_updated.isoformat())
        end_date = str((datetime.datetime.now().replace(
            microsecond=0) - datetime.timedelta(days=1)).isoformat())
        params = {
            "aggregateHours": 24,
            "combinationMethod": "aggregate",
            "startDateTime": start_date,
            "endDateTime": end_date,
            "maxStations": -1,
            "maxDistance": -1,
            "contentType": "json",
            "unitGroup": "metric",
            "locationMode": "array",
            "key": config.weather_key,
            "dataElements": "default",
            "shortColumnNames": False,
            "locations": city
        }
        response = requests.get(glbs.WEATHER_URL, params=params)
        if response.status_code == 200:
            weather_data = response.json()
            # Renaming the col names to the full names
            rename = {}
            for col in weather_data['columns'].keys():
                rename[col] = weather_data['columns'][col]['name']
            # Converting dict to dataframe
            df = pd.DataFrame(weather_data['locations'][0]['values'])
            df['Name'] = weather_data['locations'][0]['name']
            df = df.rename(columns=rename)
            df = df.where(pd.notnull(df), None)
            df['Date time'] = pd.to_datetime(
                df['Date time'], unit='ms').dt.strftime("%m/%d/%Y")
            return df
        else:
            raise Exception(
                f"[Response: {response.status_code}] Unable to retrieve weather data from VisualCrossing")
    except Exception as ex:
        raise ex


def append_csv(csv_path, dataframe):
    '''
    Append the csv with new rows of information
    :param csv_path: path to csv
    :param dataframe: dataframe of rows to be appended
    :type csv_path: str
    :type dataframe: dataframe
    '''
    try:
        init = pd.read_csv(csv_path)
        to_write = pd.concat([init, dataframe], ignore_index=True)
        to_write.to_csv(csv_path, index=False)
        # print(f"'{csv_path}' has been updated!")
    except Exception as ex:
        raise ex


def update_bookings(bookings, weather_df, city):
    '''
    Update bookings with weather data
    :param bookings: dictionary of booking data
    :param weather_df: dataframe of weather information
    :param city: city of weather data
    :type bookings: dict
    :type weather_df: dataframe
    :type city: str
    '''
    try:
        # Update the corresponding locations with weather data
        locations = []
        if city == 'Ottawa':
            locations = ['Altitude Kanata', 'Coyote Rock Gym']
        elif city == 'Gatineau':
            locations = ['Altitude Gatineau']
        else:
            raise Exception(f"Unsupported city: {city}")

        # Loop through all bookings and update the data, if not present
        for row in bookings:
            # Only add weather data to that match the weather location, and do not already have weather data
            if row['location'] in locations and (not row.keys() in ['Maximum Temperature', 'Minimum Temperature', 'Temperature', 'Wind Chill', 'Heat Index', 'Precipitation', 'Snow Depth']):
                # reformat the date from json
                date = datetime.datetime.fromisoformat(
                    row['retrieved_at']).strftime(("%Y-%m-%d"))
                # Look for the corresponding date in the weather CSv, if not there skip
                weather = weather_df.loc[weather_df['date'] == date]
                if weather.shape[0] >= 1:
                    for col in list(weather):
                        if weather.shape[0] > 1:
                            print(
                                "Warning: More than one value found for weather, using last")
                            row[col] = weather.iloc[-1][col]
                        else:
                            row[col] = weather.iloc[0][col]
                else:
                    # print(f"No weather data found for {date}")
                    pass
        common.write_bulk_api(bookings, os.path.join(
            glbs.ES_BULK_DATA, 'bookings.json'), 'bookings')
    except Exception as ex:
        raise ex


def import_weather(csv_dir):
    '''
    Import and clean CSV weather data to insert into booking
    :param csv_dir: Path to weather csv
    :type csv_dir: str
    :return: dataframe of weather csv
    :rtype: dataframe
    '''
    try:
        # Reformating col names, and cleaning data
        init = pd.read_csv(csv_dir)
        init.columns = init.columns.str.strip().str.lower().str.replace(' ', '_')
        init = init.rename(columns={'name': 'city', 'date_time': 'date'})
        df = init.where(pd.notnull(init), None)
        df['date'] = pd.to_datetime(
            df['date']).dt.strftime("%Y-%m-%d")
        return df
    except Exception as ex:
        raise ex


def main():
    current_time = str(datetime.datetime.now().isoformat())
    bookings = get_bookings()
    last_ottawa = last_updated('Ottawa')
    last_gat = last_updated('Gatineau')
    # Check if data is already up to date
    if last_ottawa.date() == (datetime.datetime.now() - datetime.timedelta(days=1)).date() or last_gat.date() == (datetime.datetime.now() - datetime.timedelta(days=1)).date():
        raise Exception(f"The weather data is already up to date")
    # Otherwise get new weather data
    ott = get_weather('Ottawa', last_ottawa)
    gat = get_weather('Gatineau', last_gat)
    # Update Weather CSVs
    append_csv(glbs.OTTAWA_WEATHER, ott)
    append_csv(glbs.GATINEAU_WEATHER, gat)
    # Update Bookings JSONs
    update_bookings(bookings, import_weather(glbs.OTTAWA_WEATHER), 'Ottawa')
    update_bookings(bookings, import_weather(
        glbs.GATINEAU_WEATHER), 'Gatineau')
    print(f"[{current_time}] Bookings successfully updated")


if __name__ == "__main__":
    main()
