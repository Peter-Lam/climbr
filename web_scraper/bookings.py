#!/usr/bin/python3

# --------------------------------
# Tool used to gather Altitude's session availability from their booking website
# --------------------------------

import argparse
import os
import pathlib
import platform
import sys
import traceback
from datetime import datetime
from time import sleep

import firebase_admin
import requests
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver import Chrome

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


def get_bookings(driver, location, capacity, url, zone=None):
    """
    Gathering the booking information based on the location
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
        except Exception:
            pass
        selected_day = int(
            driver.find_element_by_xpath("//a[contains(@class,'ui-state-active')]").text
        )
        if selected_day != current_day:
            raise Exception(
                f"[{current_time}] Unable to select the current date... Selected {selected_day} instead"
            )
        sleep(5)
        # Find the first time slot and it's availability
        time_slot = driver.find_element_by_class_name(
            "offering-page-schedule-list-time-column"
        ).text
        availability = driver.find_element_by_xpath(
            "//td[@class='offering-page-schedule-list-time-column']/following-sibling::td"
        ).text

        # Checking availability
        if "Full" in availability:
            availability = 0
        # For Gatineau location, this means 50-75 available spots. Since leaving it NULL will skew, and there is no way to calculate the spots
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
            except ValueError as ex:
                print(
                    f"[{current_time}] Warning: Unpredicted format, `{availability}`, ignoring conversion to integer"
                )

        # Parsing data
        __, date, time = time_slot.split(",")
        month, day = date.strip().split()

        # # If dates don't match up, then manually set the next session time, assuming the availability is 0
        # if int(day) != current_day:
        #     # Get the last session time from JSON and set the time to the next session time
        #     last_booking = common.get_last_document(OUTPUT_FILE)
        #     last_session = last_booking['time_slot']
        #     next_session = time_slots[time_slots.index(last_session)+1]
        #     # Overwrite the time slot
        #     time = next_session
        #     availability = 0
        #     print(
        #         f"[{current_time}] WARNING: Unable to select the current date. Assuming session is full, and continuing...")

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
    Starting the appropriate webdriver and returning a selenium driver to web scraping
    :param driver:
    """
    # Setting up chromedriver depending on OS
    webdriver_path = None
    if platform.system() == "Windows":
        webdriver_path = os.path.join(glbs.WEB_SCRAPER_DIR, "chromedriver.exe")
    elif platform.system() == "Linux":
        if "DOCKER_SCRAPER" not in os.environ:
            print(
                "Docker container not detected, this script may not work as intended. For full support, please create a container with 'docker-compose up'"
            )
        webdriver_path = "/usr/bin/chromedriver"
    else:
        raise Exception(f"{platform.system()} is not supported")
    # Using Selenium to read the website
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=chrome_options, executable_path=webdriver_path)


def update_firestore(booking):
    """
    Update firestore db with booking information
    :param booking: booking information
    :type booking: dict
    """
    try:
        doc_ref = db.collection("booking").document()
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
        # If there is weather data, then remove and reference it to 'weather' collection if it's not already there
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
            # If the weather data already exists, just reference it in bookings otherwise add to weather db
            if weather_docs:
                # Get the most recent weather document that matches the date
                weather_ref = weather_docs[-1]
            # Otherwise add new weather data, and get reference
            else:
                weather_ref = db.collection("weather").document()
                weather_ref.set(weather)
                print(
                    f"[{str(datetime.now().isoformat())}] [Document ID: {weather_ref.id}] {weather['city']}'s weather data has been added to the db "
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
            f"[{str(datetime.now().isoformat())}] ['{location_name}'] [Document ID: {booking_ref.id}] Session info successfully retrieved and added to Firestore"
        )
    except Exception as ex:
        raise ex


def main():
    """
    Main Script
    """
    try:
        args = cmd_args.init()
        # Variables
        locations = {
            "Altitude Kanata": {
                "url": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=3b34573ebf36421fb31011f8dc557032&random=60f0fa980c2c2&iframeid=&mode=p",
                "capacity": 250,
            },
            "Altitude Gatineau": {
                "url": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=a443ee2f171e442b99079327c2ef6fc1&random=5f57c64752a17&iframeid=&mode=p",
                "capacity": 85,
            },
            "Coyote Rock Gym": {
                "url": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=e99cbc88382e4b269eabe0cf45e111a7&random=5f792b35f0651&iframeid=&mode=p",
                "capacity": 80,
            },
        }
        driver = get_driver()
        for name in args.locations:
            name = name.replace("_", " ").strip()
            # Altitude made booking adjustments because of COVID-19 spike and restrictions
            # If it's a weekday && before 3 then it's 1 booking, otherwise it's by 3 locations
            # Disabling since Gatineau is back to 1 area booking
            if False and (
                (
                    name == "Altitude Gatineau"
                    and datetime.now().weekday() < 5
                    and datetime.now().hour >= 3
                )
                or (name == "Altitude Gatineau" and datetime.now().weekday() >= 5)
            ):
                # Hard coding the values here because this is likely a temp change for ~month
                annex_url = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=de8bf81d740342e1a78e87f68ef74135&widget_guid=0769717ed49c4aa2b4549477104a14b1&random=5ff1585a9b149&iframeid=&mode=p"
                main_url = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=2fe86937914e4782a90eb92f023ed83a&widget_guid=0769717ed49c4aa2b4549477104a14b1&random=5ff1585a9b078&iframeid=&mode=p"
                basement_url = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=9dc37e9f88d441ee84bd6681ec792574&widget_guid=0769717ed49c4aa2b4549477104a14b1&random=5ff1585a9b207&iframeid=&mode=p"
                annex_booking = get_bookings(driver, name, 20, annex_url, zone="Annex")
                main_booking = get_bookings(driver, name, 25, main_url, zone="Main")
                basement_booking = get_bookings(
                    driver, name, 20, basement_url, zone="Basement"
                )
                # Combine the all booking zones together
                combined_booking = annex_booking.copy()
                combined_booking["availability"] += (
                    main_booking["availability"] + basement_booking["availability"]
                )
                combined_booking["reserved_spots"] += (
                    main_booking["reserved_spots"] + basement_booking["reserved_spots"]
                )
                combined_booking["capacity"] += (
                    main_booking["capacity"] + basement_booking["capacity"]
                )
                combined_booking["zone"] = None
                # Log the data for zones - incase we want to visualize, and a combined data for general purposes
                for booking in [
                    annex_booking,
                    main_booking,
                    basement_booking,
                    combined_booking,
                ]:
                    common.update_bulk_api(booking, OUTPUT_FILE, "bookings")
            # Coyote Adjustments for COVID-19 REd ZOne Response - Multi zone like Altitude
            elif False and (name == "Coyote Rock Gym"):
                zone_1 = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=c8f63096988b457891da8442931ebc11&random=60549c429b3d6&iframeid=&mode=p"
                zone_2 = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=0a283f4776ed45eda69e8bf57d59d65f&random=60549c4451ff3&iframeid=&mode=p"
                zone_3 = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=0d52f12114a7498cb92bbbe0d8c28d16&random=60549c45b97f9&iframeid=&mode=p"
                zone_4 = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=94c9afedbbdd4d7c8f15f4af863fba39&random=60549c470309e&iframeid=&mode=p"
                zone_5 = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=f9e486d095fa47dc87a45fcc57b8daab&random=6055fc64e1b8e&iframeid=&mode=p"
                zone_1_booking = get_bookings(
                    driver,
                    name,
                    10,
                    zone_1,
                    zone="Zone 1 - All topropes on the Blue, Green, and Blue Island walls",
                )
                zone_2_booking = get_bookings(
                    driver, name, 10, zone_2, zone="Zone 2 - Yellow area and Red Cave"
                )
                zone_3_booking = get_bookings(
                    driver, name, 10, zone_3, zone="Zone 3 - Boulder and Upstairs Caves"
                )
                zone_4_booking = get_bookings(
                    driver, name, 10, zone_4, zone="Zone 4 - North Wall Area"
                )
                zone_5_booking = get_bookings(
                    driver, name, 2, zone_5, zone="Zone 5 - Fitness Room"
                )
                # Combine the two booking information
                coyote_combined_booking = zone_1_booking.copy()
                coyote_combined_booking["availability"] += (
                    zone_2_booking["availability"]
                    + zone_3_booking["availability"]
                    + zone_4_booking["availability"]
                    + zone_5_booking["availability"]
                )
                coyote_combined_booking["reserved_spots"] += (
                    zone_2_booking["reserved_spots"]
                    + zone_3_booking["reserved_spots"]
                    + zone_4_booking["reserved_spots"]
                    + zone_5_booking["reserved_spots"]
                )
                coyote_combined_booking["capacity"] += (
                    zone_2_booking["capacity"]
                    + zone_3_booking["capacity"]
                    + zone_4_booking["capacity"]
                    + zone_5_booking["capacity"]
                )
                coyote_combined_booking["zone"] = None
                # Log the data for zones - incase we want to visualize, and a combined data for general purposes
                for booking in [
                    zone_1_booking,
                    zone_2_booking,
                    zone_3_booking,
                    zone_4_booking,
                    zone_5_booking,
                    coyote_combined_booking,
                ]:
                    common.update_bulk_api(booking, OUTPUT_FILE, "bookings")
            # Otherwise just gather bookings normally
            else:
                booking = get_bookings(
                    driver, name, locations[name]["capacity"], locations[name]["url"]
                )
                # Logging and saving info
                common.update_bulk_api(booking, OUTPUT_FILE, "bookings")
            # If the config file is setup, push to Firestore too
            if config.firestore_json:
                update_firestore(booking)
        driver.quit()
        # Initialize ES and Kibana urls depending on if it's running in Docker or host
        es_url = (
            glbs.ES_URL if "DOCKER_SCRAPER" not in os.environ else glbs.ES_URL_DOCKER
        )
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
                    f"WARNING: Unable to update bookings to Elasticsearch. Please use 'climb.py update' to manually update the information. no such index [bookings]"
                )
            else:
                print(
                    f"WARNING: Unable to update bookings to Elasticsearch. Please use 'climb.py update' to manually update the information \n{ex}"
                )
        print(
            f"[{str(datetime.now().isoformat())}] {args.locations} Session info successfully retrieved and added to '{OUTPUT_FILE}', view results on port 5601"
        )
    except Exception as ex:
        raise ex


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
