#!/usr/bin/python3

# --------------------------------
# Tool used to gather Altitude's session availablitiy from their booking website
# --------------------------------

import argparse
import pathlib
import os
import platform
import sys
import requests
sys.path.append('../')
import common.common as common
from datetime import datetime
from selenium import webdriver
from selenium.webdriver import Chrome

PROJECT_DIR = pathlib.Path(__file__).parent.absolute()
PARENT_DIR = os.path.dirname(PROJECT_DIR)
def main():
    '''
    Main Script
    '''
    try:
        # Variables
        output_log = os.path.join(PARENT_DIR, 'logs', 'bookings.log')
        output_file = os.path.join(PARENT_DIR, 'data','output','bookings.json')
        webpage = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=90a6abd5e5124f7384b2b60d00683e3d&random=5f1483d0c152d&iframeid=&mode=p"
        date_obj = datetime.now()
        current_time = str(date_obj)
        current_year = str(date_obj.year)
        current_day = date_obj.day

        # Setting up chromedriver depending on OS
        webdriver_path = None
        if platform.system() == 'Windows':
            webdriver_path = os.path.join(PROJECT_DIR, 'chromedriver.exe')
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
        driver = webdriver.Chrome(options=chrome_options, executable_path=webdriver_path)
        driver.get(webpage)
        
        # Click on the current date, find the selected date and verify 
        driver.find_element_by_xpath("//td[contains(@class,'ui-datepicker-today')]").click()
        selected_day = int(driver.find_element_by_xpath("//a[contains(@class,'ui-state-active')]").text)
        if not selected_day is current_day:
            # raise Exception(f"[{current_time}] Unable to select the current date...")
            pass
        
        # Find the first time slot and it's availability
        time_slot = driver.find_element_by_class_name('offering-page-schedule-list-time-column').text
        availability = driver.find_element_by_xpath("//td[@class='offering-page-schedule-list-time-column']/following-sibling::td").text

        # Parsing data
        __, date, time = time_slot.split(',')
        start = time.split('to')[0].strip()
        end = time.split('to')[1].strip()

        # Converting to HH:MM AM/PM format
        start = common.convert_to_hhmm(start)
        end = common.convert_to_hhmm(end)

        # Checking availability
        if 'Full' in availability:
            availability = 0
        else:
            try:
                availability = int(availability.replace('Availability', '').replace('spaces', '').replace('space', '').strip('\n').strip())
            except ValueError as ex:
                print(f"[{current_time}] Warning: Unpredicted format, `{availability}`, ignoring conversion to integer")
        booking = {'date': date.strip(),
                   'year': current_year,
                   'time_slot': time.strip(),
                   'start_time': start,
                   'end_time': end,
                   'availability': availability,
                   'retrieved_at': current_time}
        
        # Logging and saving info
        common.write_log(f"Retrieved session at {current_time}", output_log)
        common.update_bulk_api(booking, output_file, 'bookings')
        print(f"[{current_time}] Session info successfully retrieved! See information at '{output_file}'")

        driver.quit()
    except Exception as ex:
        driver.quit()
        raise ex
if __name__ == "__main__":
    main()