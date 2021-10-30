#!/usr/bin/python3
"""Tool used to gather Altitude's session availability from their booking website."""

import os
import platform
import sys
import traceback
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import common.common as common  # noqa
import common.globals as glbs  # noqa
import common.validate as validate  # noqa
import config as config  # noqa
import web_scraper.utils.args as cmd_args  # noqa

OUTPUT_FILE = os.path.join(glbs.ES_BULK_DATA, "bookings.json")
if config.firestore_json:
    db = common.connect_to_firestore()


def get_capacity(driver, location, url):
    """
    Gather the live occupancy numbers based on the location.

    :param driver: Selenium driver
    :param location: The location of the climbing gym
    :param capacity: The max capacity of a climbing gym
    :param url: Rockgympro booking url
    :type driver: driver
    :type location: str
    :type capacity: int
    :type url: str
    :return: Booking infomation
    :rtype: dict
    """
    # Getting the current time
    driver.get(url)
    sleep(10)
    current_datetime = datetime.now()

    # Grab data from website
    try:
        reserved_spots = int(driver.find_element(By.ID, "count").text)
        capacity = int(driver.find_element(By.ID, "capacity").text.strip("of").strip())
        percent_full = (reserved_spots / capacity) * 100
    # Take a screenshot if there is an error
    except NoSuchElementException as ex:
        file_name_date = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        image_name = f"webscraper_{location.lower()}_{file_name_date}.png"
        driver.save_screenshot(os.path.join(glbs.IMAGE_LOG_DIR, image_name))
        raise ex

    booking = {
        "location": location,
        "month": current_datetime.strftime("%B"),
        "day_of_week": current_datetime.strftime("%A"),
        "day": str(current_datetime.day),
        "year": str(current_datetime.year),
        "start_time": current_datetime.strftime("%I:%M %p"),
        "start_hour": current_datetime.hour,
        "start_minute": current_datetime.minute,
        "end_time": current_datetime.strftime("%I:%M %p"),
        "availability": capacity - reserved_spots,
        "reserved_spots": reserved_spots,
        "capacity": capacity,
        "percent_full": percent_full,
        "retrieved_at": datetime.now().isoformat(),
    }
    return booking


def get__rgpro_bookings(driver, location, capacity, url, zone=None):
    """
    Gather booking information from RGPro based on the location.

    :param driver: Selenium driver
    :param location: The location of the climbing gym
    :param capacity: The max capacity of a climbing gym
    :param url: Rockgympro booking url
    :param zone: Optional zone/subsection of gym
    :type driver: driver
    :type location: str
    :type capacity: int
    :type url: str
    :return: Booking infomation
    :rtype: dict
    """
    try:
        # Getting the current time
        current_time = str(datetime.now().isoformat())
        current_year = str(datetime.now().year)
        current_day = datetime.now().day
        current_day_of_week = datetime.now().strftime("%A")

        driver.get(url)
        # Click on the current date, find the selected date and verify
        try:
            driver.find_element_by_xpath(
                "//td[contains(@class,'ui-datepicker-today')]"
            ).click()
        except Exception:  # noqa
            pass  # noqa
        selected_day = int(
            driver.find_element_by_xpath("//a[contains(@class,'ui-state-active')]").text
        )
        if selected_day != current_day:
            raise Exception(
                f"[{current_time}] Unable to select the current date..."
                f" Selected {selected_day} instead"
            )
        sleep(5)
        # Find the first time slot and it's availability
        time_slot = driver.find_element_by_class_name(
            "offering-page-schedule-list-time-column"
        ).text
        availability = driver.find_element_by_xpath(
            "//td[@class='offering-page-schedule-list-time-column']/following-sibling::td"  # noqa
        ).text

        # Checking availability
        if "Full" in availability:
            availability = 0
        # Choosing to set availability 1/2 way between 50 and 75 (max)
        elif "Available" in availability:
            availability = (capacity - 50) / 2 + 50
        else:
            try:
                availability = int(
                    availability.replace("Availability", "")
                    .replace("spaces", "")
                    .replace("space", "")
                    .strip("\n")
                    .strip()
                )
            except ValueError:
                print(
                    f"[{current_time}] Warning: Unpredicted format,"
                    f" `{availability}`, ignoring conversion to integer."
                )

        # Parsing data
        __, date, time = time_slot.split(",")
        month, day = date.strip().split()

        # Parse time slot to start and end times
        start = time.split("to")[0].strip()
        end = time.split("to")[1].strip()

        # Converting to HH:MM AM/PM format
        start = common.convert_to_hhmm(start)
        end = common.convert_to_hhmm(end)
        booking = {
            "location": location,
            "month": month.strip(),
            "day_of_week": current_day_of_week,
            "day": day.strip(),
            "year": current_year,
            "time_slot": time.strip(),
            "start_time": start,
            "start_hour": int(common.str_to_time(start).hour),
            "start_minute": int(common.str_to_time(start).minute),
            "end_time": end,
            "availability": availability,
            "reserved_spots": capacity - availability
            if availability is not None
            else None,
            "capacity": capacity,
            "zone": zone,
            "retrieved_at": current_time,
        }
        return booking
    except Exception as ex:
        driver.quit()
        print(f"Unable to get booking information for: {location}")
        raise ex


def get_driver():
    """
    Start the appropriate webdriver.

    Return a selenium driver to web scrape.
    """
    # Setting up chromedriver depending on OS
    webdriver_path = None
    if platform.system() == "Windows":
        webdriver_path = os.path.join(glbs.WEB_SCRAPER_DIR, "chromedriver.exe")
    elif platform.system() == "Linux":
        if "DOCKER_SCRAPER" not in os.environ:
            print(
                "Docker container not detected, this script may not work as intended."
                " For full support, please create a container with 'docker-compose up'."
            )
        webdriver_path = "/usr/bin/chromedriver"
    else:
        raise Exception(f"{platform.system()} is not supported")
    # Using Selenium to read the website
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")

    return webdriver.Chrome(service=Service(webdriver_path), options=chrome_options)


def update_firestore(booking):
    """
    Update firestore db with booking information.

    :param booking: booking information
    :type booking: dict
    """
    try:
        weather_keys = [
            "maximum_temperature",
            "minimum_temperature",
            "temperature",
            "wind_chill",
            "heat_index",
            "precipitation",
            "snow_depth",
            "wind_speed",
            "wind_gust",
            "visibility",
            "cloud_cover",
            "relative_humidity",
            "conditions",
            "weather_type",
        ]
        # Local variable for every booking
        weather = {}
        weather_ref = None
        # Remove weather data and reference it to 'weather' collection
        # If it's not already there
        if set(weather_keys).issubset(booking.keys()):
            # Move weather data to a new dict
            for key in weather_keys:
                weather[key] = booking.pop(key)
            # Copy shared information to weather document
            weather["date"] = booking["date"]
            weather["datetimestr"] = booking["datetimestr"]
            weather["city"] = booking["city"]
            # Query for existing weather data
            weather_docs = (
                db.collection("weather")
                .where("date", "==", booking["date"])
                .where("city", "==", booking["city"])
                .get()
            )
            # Reference data if exists, otherwise add to weather db
            if weather_docs:
                # Get the most recent weather document that matches the date
                weather_ref = weather_docs[-1]
            # Otherwise add new weather data, and get reference
            else:
                weather_ref = db.collection("weather").document()
                weather_ref.set(weather)
                print(
                    f"[{str(datetime.now().isoformat())}]"
                    f" [Document ID: {weather_ref.id}] {weather['city']}'s"
                    " weather data has been added to the db."
                )

        # Referencing location and weather
        locations = (
            db.collection("locations").where("name", "==", booking["location"]).get()
        )
        booking["location_ref"] = (
            db.collection("locations").document(locations[0].id) if locations else None
        )
        booking["weather_ref"] = (
            db.collection("weather").document(weather_ref.id) if weather_ref else None
        )
        # Storing string version of their id's
        booking["location_id"] = locations[0].id if locations else None
        booking["weather_id"] = weather_ref.id if weather_ref else None
        # Removing Location data - No longer need because of reference
        location_name = booking["location"]
        del booking["location"]
        # Push new document to bookings collection
        booking_ref = db.collection("bookings").document()
        booking_ref.set(booking)
        print(
            f"[{str(datetime.now().isoformat())}] ['{location_name}']"
            f" [Document ID: {booking_ref.id}] Session info successfully "
            "retrieved and added to Firestore."
        )
    except Exception as ex:
        raise ex


def update_es(location):
    """Update newly data to Elasticsearch and Kibana."""
    # Initialize ES and Kibana urls depending on if it's running in Docker or host
    es_url = glbs.ES_URL if "DOCKER_SCRAPER" not in os.environ else glbs.ES_URL_DOCKER
    kibana_url = (
        glbs.KIBANA_URL
        if "DOCKER_SCRAPER" not in os.environ
        else glbs.KIBANA_URL_DOCKER
    )
    try:
        # Preparing Elasticsearch and Kibana for data consumption
        common.create_index(
            es_url,
            "bookings",
            validate.file(os.path.join(glbs.ES_MAPPINGS, "bookings_mapping.json")),
            silent=True,
            force=True,
        )
        common.create_index_pattern(kibana_url, "bookings", silent=True, force=True)
        # Uploading data into Elasticsearch
        common.upload_to_es(es_url, OUTPUT_FILE, silent=True)
    except Exception as ex:
        if "index_not_found_exception: no such index [bookings]" in ex:
            print(
                "WARNING: Unable to update bookings to Elasticsearch."
                " Please use 'climb.py update' to manually update the information."
                " No such index [bookings]"
            )
        else:
            print(
                "WARNING: Unable to update bookings to Elasticsearch."
                " Please use 'climb.py update' to manually update"
                f" the information\n{ex}"
            )
    print(
        f"[{str(datetime.now().isoformat())}] {location}"
        " Session info successfully retrieved and added to"
        f" '{OUTPUT_FILE}', view results on port 5601"
    )


def main():
    """Get reservation data based on command args."""
    args = cmd_args.init()
    # Variables
    locations = {
        "Altitude Gatineau": {
            "url": "https://portal.rockgympro.com/portal/public/d8debad49996f64b9734856be4913a25/occupancy?&iframeid=occupancyCounter&fId=1658",  # noqa
        },
    }
    driver = get_driver()
    for name in args.locations:
        name = name.replace("_", " ").strip()
        booking = get_capacity(driver, name, locations[name]["url"])
        # Logging and saving info
        common.update_bulk_api(booking, OUTPUT_FILE, "bookings")
        # If the config file is setup, push to Firestore too
        if config.firestore_json:
            update_firestore(booking)
    driver.quit()
    update_es(args.locations)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        # Send an email alert of error if config.py is setup
        if config.smpt_email and config.smpt_pass and config.to_notify:
            common.send_email(
                config.smpt_email,
                config.smpt_pass,
                config.to_notify,
                f"[{str(datetime.now())}] Error in bookings.py",
                os.path.join(glbs.EMAIL_TEMPLATE_DIR, "error_notification"),
                "".join(traceback.TracebackException.from_exception(ex).format()),
                common.get_files(glbs.LOG_DIR, ".*"),
            )
        raise ex
