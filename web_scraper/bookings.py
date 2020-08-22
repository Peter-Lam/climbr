#!/usr/bin/python3

# --------------------------------
# Tool used to gather Altitude's session availablitiy from their booking website
# --------------------------------

import requests
import sys
import platform
import os
import pathlib
import argparse

from datetime import datetime
from selenium import webdriver
from selenium.webdriver import Chrome

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import common.globals as glbs  # noqa
import common.common as common  # noqa


def main():
    '''
    Main Script
    '''
    try:
        # Variables
        output_log = os.path.join(glbs.LOG_DIR, '.bookings.log')
        output_file = os.path.join(glbs.OUTPUT_DIR, 'bookings.json')
        webpage = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=90a6abd5e5124f7384b2b60d00683e3d&random=5f1483d0c152d&iframeid=&mode=p"
        date_obj = datetime.now()
        current_time = str(date_obj.isoformat())
        current_year = str(date_obj.year)
        current_day = date_obj.day
        current_day_of_week = date_obj.strftime('%A')
        time_slots = ['10 AM to 11:45 AM', '12:05 PM to 1:50 PM', '2:10 PM to 3:55 PM',
                      '4:15 PM to 6 PM', '6:20 PM to 8:05 PM', '8:25 PM to 10:10 PM']

        # Setting up chromedriver depending on OS
        webdriver_path = None
        if platform.system() == 'Windows':
            webdriver_path = os.path.join(
                glbs.WEB_SCRAPER_DIR, 'chromedriver.exe')
        elif platform.system() == 'Linux':
            if 'DOCKER_SCRAPER' not in os.environ:
                print("Docker container not detected, this script may not work as intended. For full support, please create a container with 'docker-compose up'")
            webdriver_path = '/usr/bin/chromedriver'
        else:
            raise Exception(f"{platform.system()} is not supported")

        # Using Selenium to read the website
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(
            options=chrome_options, executable_path=webdriver_path)
        driver.get(webpage)

        # Click on the current date, find the selected date and verify
        driver.find_element_by_xpath(
            "//td[contains(@class,'ui-datepicker-today')]").click()
        selected_day = int(driver.find_element_by_xpath(
            "//a[contains(@class,'ui-state-active')]").text)
        if selected_day != current_day:
            raise Exception(
                f"[{current_time}] Unable to select the current date... Selected {selected_day} instead")

        # Find the first time slot and it's availability
        time_slot = driver.find_element_by_class_name(
            'offering-page-schedule-list-time-column').text
        availability = driver.find_element_by_xpath(
            "//td[@class='offering-page-schedule-list-time-column']/following-sibling::td").text

        # Checking availability
        if 'Full' in availability:
            availability = 0
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

        # If dates don't match up, then manually set the next session time, assuming the availability is 0
        if int(day) != current_day:
            # Get the last session time from JSON and set the time to the next session time
            last_booking = common.get_last_document(output_file)
            last_session = last_booking['time_slot']
            next_session = time_slots[time_slots.index(last_session)+1]
            # Overwrite the time slot
            time = next_session
            availability = 0
            print(
                f"[{current_time}] WARNING: Unable to select the current date. Assuming session is full, and continuing...")
            # TODO: Screenshot this with selenium for logs

        # Parse time slot to start and end times
        start = time.split('to')[0].strip()
        end = time.split('to')[1].strip()

        # Converting to HH:MM AM/PM format
        start = common.convert_to_hhmm(start)
        end = common.convert_to_hhmm(end)

        booking = {'month': month.strip(),
                   'day_of_week': current_day_of_week,
                   'day': day.strip(),
                   'year': current_year,
                   'time_slot': time.strip(),
                   'start_time': start,
                   'end_time': end,
                   'availability': availability,
                   'retrieved_at': current_time}

        # Logging and saving info
        common.write_log(f"Retrieved session at {current_time}", output_log)
        common.update_bulk_api(booking, output_file, 'bookings')
        print(
            f"[{current_time}] Session info successfully retrieved! See information at '{output_file}'")

        driver.quit()
    except Exception as ex:
        driver.quit()
        raise ex


if __name__ == "__main__":
    main()
