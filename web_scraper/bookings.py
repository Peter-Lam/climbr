#!/usr/bin/python3

# --------------------------------
# Tool used to gather Altitude's session availablitiy from their booking website
# --------------------------------

import argparse
import datetime
import pathlib
import os
import platform
import sys
import requests
sys.path.append('../')
import common.common as common

from selenium import webdriver
from selenium.webdriver import Chrome

PROJECT_DIR = pathlib.Path(__file__).parent.absolute()

def main():
    '''
    Main Script
    '''
    try:
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
        # Declaring variables
        webpage = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=90a6abd5e5124f7384b2b60d00683e3d&random=5f1483d0c152d&iframeid=&mode=p"
        current_time = str(datetime.datetime.now())
        year = str(datetime.datetime.now().year)

        # Using Selenium to read the website
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=chrome_options, executable_path=webdriver_path)
        driver.get(webpage)
        
        # Find the first time slot and it's availability
        time_slot = driver.find_element_by_class_name('offering-page-schedule-list-time-column').text
        availability = driver.find_element_by_xpath("//td[@class='offering-page-schedule-list-time-column']/following-sibling::td").text
        driver.quit()

        # Parsing data
        __, date, time = time_slot.split(',')
        start, end = time.split('to')
        availability = int(availability.replace('Availability', '').replace('spaces', '').strip('\n').strip())
        booking = {'date': date.strip(),
                   'year': year,
                   'time_slot': time.strip(),
                   'start_time': start.strip(),
                   'end_time': end.strip(),
                   'availability': availability,
                   'retrieved_at': current_time}
        # Logging and saving info
        common.write_log(f"Retrieved session at {current_time}", os.path.join(PROJECT_DIR, 'bookings.log'))
        common.update_bulk_api(booking, os.path.join(os.path.dirname(PROJECT_DIR), 'elasticsearch_files','bookings.json'), 'bookings')

    except Exception as ex:
        # driver.quit()
        raise ex
if __name__ == "__main__":
    main()