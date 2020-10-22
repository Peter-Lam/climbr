#!/usr/bin/python3

# --------------------------------
# Tool used to gather Altitude's session availability from their booking website
# --------------------------------

import requests
import sys
import platform
import os
import pathlib
import argparse
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver import Chrome

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import common.globals as glbs  # noqa
import common.common as common  # noqa
import common.validate as validate  # noqa
import web_scraper.utils.args as cmd_args  # noqa

OUTPUT_FILE = os.path.join(glbs.ES_BULK_DATA, 'bookings.json')


def get_bookings(driver, location, capacity, url, zone=None):
    '''
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
    '''
    try:
        # Getting the current time
        current_time = str(datetime.now().isoformat())
        current_year = str(datetime.now().year)
        current_day = datetime.now().day
        current_day_of_week = datetime.now().strftime('%A')

        driver.get(url)
        # Click on the current date, find the selected date and verify
        driver.find_element_by_xpath(
            "//td[contains(@class,'ui-datepicker-today')]").click()
        selected_day = int(driver.find_element_by_xpath(
            "//a[contains(@class,'ui-state-active')]").text)
        if selected_day != current_day:
            raise Exception(
                f"[{current_time}] Unable to select the current date... Selected {selected_day} instead")
        sleep(5)
        # Find the first time slot and it's availability
        time_slot = driver.find_element_by_class_name(
            'offering-page-schedule-list-time-column').text
        availability = driver.find_element_by_xpath(
            "//td[@class='offering-page-schedule-list-time-column']/following-sibling::td").text

        # Checking availability
        if 'Full' in availability:
            availability = 0
        # For Gatineau location, this means 50-75 available spots. Since leaving it NULL will skew, and there is no way to calculate the spots
        # Choosing to set availability 1/2 way between 50 and 75 (max)
        elif 'Available' in availability:
            availability = 57.5
        else:
            try:
                availability = int(availability.replace('Availability', '').replace(
                    'spaces', '').replace('space', '').strip('\n').strip())
            except ValueError as ex:
                print(
                    f"[{current_time}] Warning: Unpredicted format, `{availability}`, ignoring conversion to integer")

        # Parsing data
        __, date, time = time_slot.split(',')
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
        start = time.split('to')[0].strip()
        end = time.split('to')[1].strip()

        # Converting to HH:MM AM/PM format
        start = common.convert_to_hhmm(start)
        end = common.convert_to_hhmm(end)
        booking = {'location': location,
                   'month': month.strip(),
                   'day_of_week': current_day_of_week,
                   'day': day.strip(),
                   'year': current_year,
                   'time_slot': time.strip(),
                   'start_time': start,
                   'start_hour': int(common.str_to_time(start).hour),
                   'start_minute': int(common.str_to_time(start).minute),
                   'end_time': end,
                   'availability': availability,
                   'reserved_spots': capacity-availability if availability is not None else None,
                   'capacity': capacity,
                   'zone': zone,
                   'retrieved_at': current_time}
        return booking
    except Exception as ex:
        driver.quit()
        raise ex


def get_driver():
    '''
    Starting the appropriate webdriver and returning a selenium driver to web scraping
    :param driver: 
    '''
    # Setting up chromedriver depending on OS
    webdriver_path = None
    if platform.system() == 'Windows':
        webdriver_path = os.path.join(glbs.WEB_SCRAPER_DIR, 'chromedriver.exe')
    elif platform.system() == 'Linux':
        if 'DOCKER_SCRAPER' not in os.environ:
            print("Docker container not detected, this script may not work as intended. For full support, please create a container with 'docker-compose up'")
        webdriver_path = '/usr/bin/chromedriver'
    else:
        raise Exception(f"{platform.system()} is not supported")
    # Using Selenium to read the website
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        '--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    return webdriver.Chrome(options=chrome_options, executable_path=webdriver_path)


def main():
    '''
    Main Script
    '''
    try:
        args = cmd_args.init()
        # Variables
        locations = {'Altitude Kanata': {'url': 'https://app.rockgympro.com/b/widget/?a=offering&offering_guid=90a6abd5e5124f7384b2b60d00683e3d&random=5f1483d0c152d&iframeid=&mode=p',
                                         'capacity': 50},
                     'Altitude Gatineau': {'url': 'https://app.rockgympro.com/b/widget/?a=offering&offering_guid=a443ee2f171e442b99079327c2ef6fc1&random=5f57c64752a17&iframeid=&mode=p',
                                           'capacity': 75},
                     'Coyote Rock Gym': {'url': 'https://app.rockgympro.com/b/widget/?a=offering&offering_guid=e99cbc88382e4b269eabe0cf45e111a7&random=5f792b35f0651&iframeid=&mode=p',
                                         'capacity': 50}}

        driver = get_driver()
        for name in args.locations:
            name = name.replace('_', ' ').strip()
            # Altitude made booking adjustments because of COVID-19 spike and restrictions
            if name == 'Altitude Gatineau':
                # If it's the weekend or after 4pm, then bookings are split into two sections. Get bookings for both
                if datetime.now().weekday() >= 5 or datetime.now().hour >= 14:
                    # Hard coding the values here because this is likely a temp change for ~month
                    annex_url = 'https://app.rockgympro.com/b/widget/?a=offering&offering_guid=88c1f4559dcf48a8b4db0c062faad971&widget_guid=eaffac73649e461bb5daf93c64a1167a&random=5f86760adbae7&iframeid=&mode=p'
                    main_url = 'https://app.rockgympro.com/b/widget/?a=offering&offering_guid=c3a37c2e9f0547d48351941a6634753e&widget_guid=eaffac73649e461bb5daf93c64a1167a&random=5f86760adbbaf&iframeid=&mode=p'
                    annex_booking = get_bookings(
                        driver, name, 25, annex_url, zone='Annex')
                    main_booking = get_bookings(
                        driver, name, 50, main_url, zone='Main')
                    # Combine the two booking information
                    combined_booking = annex_booking.copy()
                    combined_booking['availability'] += main_booking['availability']
                    combined_booking['reserved_spots'] += main_booking['reserved_spots']
                    combined_booking['capacity'] += main_booking['capacity']
                    combined_booking['zone'] = None
                    # Log the data for zones - incase we want to visualize, and a combined data for general purposes
                    for booking in [annex_booking, main_booking, combined_booking]:
                        common.update_bulk_api(
                            booking, OUTPUT_FILE, 'bookings')
                else:
                    weekday_url = 'https://app.rockgympro.com/b/widget/?a=offering&offering_guid=a443ee2f171e442b99079327c2ef6fc1&widget_guid=eaffac73649e461bb5daf93c64a1167a&random=5f86760adaa8f&iframeid=&mode=p'
                    booking = get_bookings(driver,
                                           name, locations[name]['capacity'], weekday_url)
                    # Logging and saving info
                    common.update_bulk_api(booking, OUTPUT_FILE, 'bookings')
            # Otherwise just gather bookings normally
            else:
                booking = get_bookings(driver,
                                       name, locations[name]['capacity'], locations[name]['url'])
                # Logging and saving info
                common.update_bulk_api(booking, OUTPUT_FILE, 'bookings')
        driver.quit()
        # Initialize ES and Kibana urls depending on if it's running in Docker or host
        es_url = glbs.ES_URL if 'DOCKER_SCRAPER' not in os.environ else glbs.ES_URL_DOCKER
        kibana_url = glbs.KIBANA_URL if 'DOCKER_SCRAPER' not in os.environ else glbs.KIBANA_URL_DOCKER
        try:
            # Preparing Elasticsearch and Kibana for data consumption
            common.create_index(es_url, 'bookings', validate.file(
                os.path.join(glbs.ES_MAPPINGS, "bookings_mapping.json")), silent=True, force=True)
            common.create_index_pattern(
                kibana_url, 'bookings', silent=True, force=True)
            # Uploading data into Elasticsearch
            common.upload_to_es(es_url, OUTPUT_FILE, silent=True)
        except Exception as ex:
            print(
                f"WARNING: Unable to update bookings to Elasticsearch. Please use 'climb.py update' to manually update the information \n{ex}")
        print(
            f"[{str(datetime.now().isoformat())}] {args.locations} Session info successfully retrieved! See information at '{OUTPUT_FILE}' or on port 5601")
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        # print(ex)
        raise ex
