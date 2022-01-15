#!/usr/bin/python3

"""Use this script to periodically update weather data to 'bookings.json'."""

import datetime
import os
import sys

import pandas as pd
import requests
from loguru import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
import common.common as common  # noqa
import common.globals as glbs  # noqa
import config as config  # noqa


def error_callback(message):
    """
    Send an email notification about a given error.

    :param message:
    :type: loguru.Message
    """
    if config.smpt_email and config.smpt_pass and config.to_notify:
        logger.info(
            "An error has occured in weather.py, "
            f"attempting to send notification to '{config.to_notify}'"
        )
        common.send_email(
            config.smpt_email,
            config.smpt_pass,
            config.to_notify,
            f"[{str(datetime.datetime.now())}] Climbr Error: weather.py",
            os.path.join(glbs.EMAIL_TEMPLATE_DIR, "error_notification"),
            message,
            common.get_files(glbs.WEB_SCRAPER_LOG_DIR, "web_scraper.log"),
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
logger.add(sys.stdout, level="INFO", format=stdout_fmt)
logfile_fmt = "[{time:YYYY-MM-DD HH:mm:ss}] {level: <8}\t{message}"
# Log file
logger.add(
    os.path.join(glbs.WEB_SCRAPER_LOG_DIR, "web_scraper.log"),
    level="DEBUG",
    format=logfile_fmt,
    rotation="monthly",
)
# Error email handling
logger.add(error_callback, filter=lambda r: r["level"].name == "ERROR")

if config.firestore_json:
    # Make a connection to Firestore
    db = common.connect_to_firestore()


def last_updated(city):
    """
    Get the date for the last CSV entry of weather info as a datetime object.

    :param city: The city to get weather data from
    :type city: str
    :return: date of the last entry
    :rtype: datetime
    """
    init = None
    if city in ["Ottawa", "Gatineau"]:
        if city == "Ottawa":
            init = pd.read_csv(glbs.OTTAWA_WEATHER)
        elif city == "Gatineau":
            init = pd.read_csv(glbs.GATINEAU_WEATHER)
        init["Date time"] = pd.to_datetime(init["Date time"])
        datetime = init.iloc[-1]["Date time"]
    else:
        logger.error(
            "That location is currently not supported. Try 'Ottawa' or 'Gatineau'"
        )
        sys.exit(1)
    return datetime


def get_bookings():
    """Retreive booking data and return the data."""
    file = os.path.join(glbs.ES_BULK_DATA, "bookings.json")
    return common.load_bulk_json(file)


def get_weather(city, last_updated):
    """
    Use visualcrossing api to get historical weather.

    Retrieves by params up until the day before the current date.
    Returning a pandas dataframe.

    :param city: city for weather data
    :param last_updated: the last weather entry that is stored locally
    :type city: str
    :type last_updated: datetime
    :return: Historical weather data
    :rtype: dataframe
    """
    last_updated += datetime.timedelta(days=1)
    start_date = str(last_updated.isoformat())
    end_date = str(
        (
            datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=1)
        ).isoformat()
    )
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
        "locations": city,
    }
    response = requests.get(glbs.WEATHER_URL, params=params)
    if response.status_code == 200:
        weather_data = response.json()
        # Renaming the col names to the full names
        rename = {}
        for col in weather_data["columns"].keys():
            rename[col] = weather_data["columns"][col]["name"]
        # Converting dict to dataframe
        df = pd.DataFrame(weather_data["locations"][0]["values"])
        df["Name"] = weather_data["locations"][0]["name"]
        df = df.rename(columns=rename)
        df = df.where(pd.notnull(df), None)
        df["Date time"] = pd.to_datetime(df["Date time"], unit="ms").dt.strftime(
            "%m/%d/%Y"
        )
        return df
    else:
        logger.error(
            f"[Response: {response.status_code}]"
            " Unable to retrieve weather data from VisualCrossing."
        )
        sys.exit(1)


def append_csv(csv_path, dataframe):
    """
    Append the csv with new rows of information.

    :param csv_path: path to csv
    :param dataframe: dataframe of rows to be appended
    :type csv_path: str
    :type dataframe: dataframe
    """
    init = pd.read_csv(csv_path)
    to_write = pd.concat([init, dataframe], ignore_index=True)
    to_write.to_csv(csv_path, index=False)


def update_bookings(bookings, weather_df, city):
    """
    Update bookings with weather data.

    :param bookings: dictionary of booking data
    :param weather_df: dataframe of weather information
    :param city: city of weather data
    :type bookings: dict
    :type weather_df: dataframe
    :type city: str
    """
    # Update the corresponding locations with weather data
    locations = []
    if city == "Ottawa":
        locations = ["Altitude Kanata", "Coyote Rock Gym"]
    elif city == "Gatineau":
        locations = ["Altitude Gatineau"]
    else:
        logger.error(f"Unsupported city: {city}")
        sys.exit(1)

    # Loop through all bookings and update the data, if not present
    for row in bookings:
        # Only add weather data to rows that match the weather location,
        # and do not already have weather data
        if row["location"] in locations and (
            not set(
                [
                    "maximum_temperature",
                    "minimum_temperature",
                    "temperature",
                    "wind_chill",
                    "heat_index",
                    "precipitation",
                    "snow_depth",
                ]
            ).issubset(row.keys())
        ):
            # reformat the date from json
            date = datetime.datetime.fromisoformat(row["retrieved_at"]).strftime(
                ("%Y-%m-%d")
            )
            # Look for the corresponding date in the weather CSV, if not there skip
            weather = weather_df.loc[weather_df["date"] == date]
            if weather.shape[0] >= 1:
                for col in list(weather):
                    if weather.shape[0] > 1:
                        logger.warning(
                            "More than one value found for weather, using last"
                        )
                        row[col] = weather.iloc[-1][col]
                    else:
                        row[col] = weather.iloc[0][col]
                    if pd.isna(row[col]):
                        row[col] = None

            else:
                logger.debug(f"No weather data found for {date}.")
                pass
    common.write_bulk_api(
        bookings, os.path.join(glbs.ES_BULK_DATA, "bookings.json"), "bookings"
    )
    # If config file is setup, update firestore too
    if config.firestore_json:
        # Get location ref ids that match the weather city data
        locations_docs = db.collection("locations").where("city", "==", city).get()
        location_ids = []
        for location in locations_docs:
            location_ids.append(location.id)
        # Look for booking data that matches the same location as weather data
        # AND doesn't have a weather reference
        bookings_docs = (
            db.collection("bookings")
            .where("weather_ref", "==", None)
            .where("location_id", "in", location_ids)
            .get()
        )
        for booking in bookings_docs:
            # Local variables
            doc = booking.to_dict()
            date = datetime.datetime.fromisoformat(doc["retrieved_at"]).strftime(
                ("%Y-%m-%d")
            )
            weather_doc = {}
            # Look for the corresponding date in the weather CSV, if not there skip
            weather_row = weather_df.loc[weather_df["date"] == date]
            if weather_row.shape[0] >= 1:
                # Loop through col of the CSV row and insert it into a weather dict
                for col in list(weather):
                    if weather.shape[0] > 1:
                        logger.warning(
                            "More than one value found for weather, using last."
                        )
                        weather_doc[col] = weather_row.iloc[-1][col]
                    else:
                        weather_doc[col] = weather_row.iloc[0][col]
                # Create a new document in the weather collection
                # Look to see if weather is in db, if not then create a new document
                weather_docs = (
                    db.collection("weather")
                    .where("date", "==", weather_doc["date"])
                    .where("city", "==", weather_doc["city"])
                    .get()
                )
                if weather_docs:
                    # Get the most recent weather document that matches the date
                    weather_ref = weather_docs[-1]
                # Create a new document if not present
                else:
                    weather_ref = db.collection("weather").document()
                    weather_ref.set(weather_doc)
                    logger.info(
                        f"[Document ID: {weather_ref.id}]"
                        f" ['{weather_doc['city']}', '{weather_doc['date']}'] "
                        "Successfully updated weather data to Firestore."
                    )
                # Update current booking with weather reference
                booking_ref = db.collection("bookings").document(booking.id)
                booking_ref.update(
                    {
                        "weather_ref": db.collection("weather").document(
                            weather_ref.id
                        ),
                        "weather_id": weather_ref.id,
                        "date": weather_doc["date"],
                        "datetimestr": weather_doc["datetimestr"],
                        "city": weather_doc["city"],
                    }
                )
                logger.debug(
                    f"[Document ID: {booking.id}] ['{weather_doc['date']}'] "
                    "Successfully referenced weather data in "
                    "bookings document in Firestore."
                )
            else:
                logger.debug(f"No weather data found for {date}")
                pass
        logger.info(
            "Successfully referenced weather data in bookings document in Firestore."
        )


def import_weather(csv_dir):
    """
    Import and clean CSV weather data to insert into booking.

    :param csv_dir: Path to weather csv
    :type csv_dir: str
    :return: dataframe of weather csv
    :rtype: dataframe
    """
    # Reformating col names, and cleaning data
    init = pd.read_csv(csv_dir)
    init.columns = init.columns.str.strip().str.lower().str.replace(" ", "_")
    init = init.rename(columns={"name": "city", "date_time": "date"})
    df = init.where(pd.notnull(init), None)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


@logger.catch
def main():
    """Retroactively update weather data."""
    if config.weather_key:
        # Check for environment variables
        for var in [
            "CLIMBR_EMAIL",
            "CLIMBR_PASS",
            "DOCKER_SCRAPER",
            "PYTHONUNBUFFERED",
            "TZ",
        ]:
            if var not in os.environ:
                try:
                    common.import_env(glbs.BOOKINGS_ENV)
                    break
                except Exception:
                    logger.warning(f"'{var}' not found as an environment variable")
        bookings = get_bookings()
        last_ottawa = last_updated("Ottawa")
        last_gat = last_updated("Gatineau")
        # Check if data is already up to date
        if (
            last_ottawa.date()
            == (datetime.datetime.now() - datetime.timedelta(days=1)).date()
            or last_gat.date()
            == (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        ):
            logger.error("The weather data is already up to date")
            sys.exit(1)
        # Otherwise get new weather data
        ott = get_weather("Ottawa", last_ottawa)
        gat = get_weather("Gatineau", last_gat)
        # Update Weather CSVs
        append_csv(glbs.OTTAWA_WEATHER, ott)
        append_csv(glbs.GATINEAU_WEATHER, gat)
        # Update Bookings JSONs
        update_bookings(bookings, import_weather(glbs.OTTAWA_WEATHER), "Ottawa")
        update_bookings(bookings, import_weather(glbs.GATINEAU_WEATHER), "Gatineau")
        logger.info("Successfully updated weather data locally")
    else:
        logger.error("No API key found for VisualCrossing in 'config.py'")
        sys.exit(1)


if __name__ == "__main__":
    main()
