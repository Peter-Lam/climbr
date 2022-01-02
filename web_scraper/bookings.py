#!/usr/bin/python3
"""Tool used to gather Altitude's session availability from their booking website."""

import os
import platform
import sys
from datetime import datetime
from time import sleep

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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


def error_callback(message):
    """
    Send an email notification about a given error.

    :param message:
    :type: loguru.Message
    """
    if config.smpt_email and config.smpt_pass and config.to_notify:
        logger.info(
            "An error has occured in bookings.py, "
            f"attempting to send notification to '{config.to_notify}'"
        )
        common.send_email(
            config.smpt_email,
            config.smpt_pass,
            config.to_notify,
            f"[{str(datetime.now())}] Climbr Error: bookings.py'",
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
stdout_fmt = "{level: <8}{message}"
logger.add(sys.stdout, level="INFO", format=stdout_fmt)
# Log file
logfile_fmt = "[{time:YYYY-MM-DD HH:mm:ss}] {level: <8}\t{message}"
logger.add(
    os.path.join(glbs.WEB_SCRAPER_LOG_DIR, "web_scraper.log"),
    level="DEBUG",
    format=logfile_fmt,
    rotation="monthly",
)
# Error email handling
logger.add(error_callback, filter=lambda r: r["level"].name == "ERROR")


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
        if "Gatineau" in location:
            data = driver.execute_script("""return data.GAT""")
            reserved_spots = int(data["count"])
            # Counter on the site is incorrect,
            # well at least not accurate to current zoning (150 vs 107)
            # capacity = int(data["capacity"])
            capacity = 83 + 24
        elif "Kanata" in location:
            data = driver.execute_script("""return data.KAN""")
            reserved_spots = int(data["count"])
            capacity = int(data["capacity"])
        else:
            logger.warning(
                f"Unable to read location: {location}, "
                "using generic parser instead..."
            )
            reserved_spots = int(driver.find_element(By.ID, "count").text)
            capacity = int(
                driver.find_element(By.ID, "capacity").text.strip("of").strip()
            )
        if reserved_spots > capacity:
            logger.warning(
                "There are more reservations than "
                f"the current allowed capcity for '{location}'. "
                "Please verify if the numbers are correct."
            )
        percent_full = (reserved_spots / capacity) * 100

    # Take a screenshot if there is an error
    except NoSuchElementException as ex:
        file_name_date = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        image_name = f"webscraper_{location.lower()}_{file_name_date}.png"
        driver.save_screenshot(os.path.join(glbs.IMAGE_LOG_DIR, image_name))
        logger.error(
            f"Unable to get capacity for {location}, "
            f"see {glbs.IMAGE_LOG_DIR} for more information."
        )
        logger.error(ex)
        sys.exit(1)
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


def get_rgpro_bookings(driver, location, capacity, url, zone=None):
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
            logger.error(
                f"Unable to select the current date... "
                f"Selected {selected_day} instead"
            )
            sys.exit(1)
        sleep(5)
        # Find the first time slot and it's availability
        try:
            time_slot = driver.find_element_by_class_name(
                "offering-page-schedule-list-time-column"
            ).text
            availability = driver.find_element_by_xpath(
                "//td[@class='offering-page-schedule-list-time-column']/following-sibling::td"  # noqa
            ).text
        except Exception:
            logger.error(f"Unable to find timeslot " f"& availability for: {location}.")
            sys.exit(1)
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
                logger.warning(
                    f"Unpredicted format, "
                    f"'{availability}', ignoring conversion to integer."
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

        reserved_spots = capacity - availability
        if reserved_spots > capacity:
            logger.warning(
                "There are more reservations than "
                f"the current allowed capcity for '{location}'. "
                "Please verify if the numbers are correct."
            )
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
            "reserved_spots": reserved_spots if availability is not None else None,
            "capacity": capacity,
            "percent_full": ((reserved_spots) / capacity) * 100,
            "zone": zone,
            "retrieved_at": current_time,
        }
        return booking
    except Exception as ex:
        driver.quit()
        logger.error(f"Unable to get booking information for: {location}")
        logger.error(ex)
        sys.exit(1)


def get_driver():
    """
    Start the appropriate webdriver.

    Return a selenium driver to web scrape.
    """
    # Setting up chromedriver depending on OS
    webdriver_path = None
    if platform.system() == "Windows":
        webdriver_path = os.path.join(glbs.WEB_SCRAPER_ENV_DIR, "chromedriver.exe")
    elif platform.system() == "Linux":
        if "DOCKER_SCRAPER" not in os.environ:
            logger.warning(
                "Docker container not detected, this script may not work as intended."
                " For full support, please create a container with 'docker-compose up'."
            )
        webdriver_path = "/usr/bin/chromedriver"
    else:
        logger.error(f"{platform.system()} is not supported")
        sys.exit(1)
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
            logger.info(
                f"[Document ID: {weather_ref.id}] {weather['city']}'s"
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
    logger.info(
        f"['{location_name}'] "
        f"[Document ID: {booking_ref.id}] Session info successfully "
        "retrieved and added to Firestore."
    )


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
            force=True,
        )
        common.create_index_pattern(kibana_url, "bookings", force=True)
        # Uploading data into Elasticsearch
        common.upload_to_es(es_url, OUTPUT_FILE)
    except Exception as ex:
        if "index_not_found_exception: no such index [bookings]" in ex:
            logger.warning(
                "Unable to update bookings to Elasticsearch. "
                "Please use 'climb.py update' to manually update the information. "
                "No such index [bookings]"
            )
        else:
            logger.warning(
                "Unable to update bookings to Elasticsearch. "
                "Please use 'climb.py update' to manually update "
                f"the information\n{ex}"
            )
    logger.info(
        f"{location} "
        "Session info successfully retrieved and added to "
        f"'{OUTPUT_FILE}', view results on port 5601"
    )


@logger.catch
def main():
    """Get reservation data based on command args."""
    args = cmd_args.init()
    # Variables
    locations = {
        "Altitude Gatineau": {
            "url": "https://portal.rockgympro.com/portal/public/d8debad49996f64b9734856be4913a25/occupancy?&iframeid=occupancyCounter&fId=1658",  # noqa
            "reservation": True,
            "zone": {
                "Annex": {
                    "url": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=88c1f4559dcf48a8b4db0c062faad971&widget_guid=ce62e0ff738e4faf8042bafa71fa48e5&random=61c1e39ab0351&iframeid=&mode=p",  # noqa
                    "capacity": 25,
                },
                "Main": {
                    "url": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=14fa372e850d43f6a725aff3e0fef115&widget_guid=ce62e0ff738e4faf8042bafa71fa48e5&random=61c1e39aae36d&iframeid=&mode=p",  # noqa
                    "capacity": 25,
                },
                "Basement": {
                    "url": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=f3613ad8e2fd436f8aff84a0fc87e6ef&widget_guid=ce62e0ff738e4faf8042bafa71fa48e5&random=61c1e39aaf518&iframeid=&mode=p",  # noqa
                    "capacity": 25,
                },
                "Training": {
                    "url": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=e686357a778843b2b4afafefb36f3e72&widget_guid=ce62e0ff738e4faf8042bafa71fa48e5&random=61c1e39ab1534&iframeid=&mode=p",  # noqa
                    "capacity": 8,
                },
            },
        },
        "Altitude Gatineau Capacity": {
            "url": "https://portal.rockgympro.com/portal/public/d8debad49996f64b9734856be4913a25/occupancy?&iframeid=occupancyCounter&fId=1658",  # noqa
            "reservation": False,
        },
        "Altitude Kanata": {
            "url": "https://portal.rockgympro.com/portal/public/d8debad49996f64b9734856be4913a25/occupancy?&iframeid=occupancyCounter&fId=1748",  # noqa
            "reservation": False,
        },
        "Coyote Rock Gym": {
            "url": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=2fdc519b5db6455f84c3a687d0a40c64&random=5f79eb6c8450f&iframeid=&mode=p",  # noqa
            "reservation": True,
            "capacity": 80,
        },
    }
    driver = get_driver()
    for name in args.locations:
        name = name.replace("_", " ").strip()
        # Used to account for 2 types of rgpro systems, capacity vs reservation
        if locations[name]["reservation"]:
            # Used to account for 2 types of booking, zones vs regular
            if "zone" in locations[name]:
                # Variable to check if first sub booking has been inserted
                first = True
                booking = None
                for zone_name in locations[name]["zone"]:
                    capacity = locations[name]["zone"][zone_name]["capacity"]
                    url = locations[name]["zone"][zone_name]["url"]
                    sub_booking = get_rgpro_bookings(
                        driver, name, capacity, url, zone=zone_name
                    )
                    if first:
                        booking = sub_booking.copy()
                        first = False
                    else:
                        booking["availability"] += sub_booking["availability"]
                        booking["reserved_spots"] += sub_booking["reserved_spots"]
                        booking["capacity"] += sub_booking["capacity"]
                        booking["percent_full"] = (
                            booking["reserved_spots"] / booking["capacity"]
                        ) * 100
                        booking["zone"] = None
                    # Updating the zone, will update the full booking after
                    common.update_bulk_api(sub_booking, OUTPUT_FILE, "bookings")
                    # If the config file is setup, push to Firestore too
                    if config.firestore_json:
                        update_firestore(sub_booking)
            else:
                booking = get_rgpro_bookings(
                    driver, name, locations[name]["capacity"], locations[name]["url"]
                )
        else:
            booking = get_capacity(
                driver, name.replace("Capacity", "").strip(), locations[name]["url"]
            )
        # Logging and saving info
        common.update_bulk_api(booking, OUTPUT_FILE, "bookings")
        # If the config file is setup, push to Firestore too
        if config.firestore_json:
            update_firestore(booking)
    driver.quit()
    update_es(args.locations)


if __name__ == "__main__":
    main()
