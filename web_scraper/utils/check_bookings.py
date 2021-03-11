#!/usr/bin/python3

# --------------------------------
# Tool used to check and alert next available booking slot
# --------------------------------
import smtplib
import ssl
import requests
import sys
import platform
import os
import pathlib
import argparse
from datetime import datetime
from time import sleep
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from selenium import webdriver
from selenium.webdriver import Chrome

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
import common.globals as glbs  # noqa
import common.common as common  # noqa
import common.validate as validate  # noqa
import web_scraper.utils.args as cmd_args  # noqa
import config as config  # noqa


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
        # Click on specific date
        elements = driver.find_elements_by_xpath("//*[contains(text(), '24')]")
        parent = None
        for child in elements:
            parent = child.find_element_by_xpath("..")
            # get_attribute() method to obtain class of parent
            if "datepicker" in parent.get_attribute("class"):
                break
            else:
                raise Exception("Date not found")
        parent.click()
        sleep(5)
        # Find the first time slot and it's availability
        time_slot = driver.find_element_by_class_name(
            'offering-page-schedule-list-time-column').text
        availability = driver.find_element_by_xpath(
            "//td[@class='offering-page-schedule-list-time-column']/following-sibling::td").text
        # Checking availability
        if 'Full' in availability:
            availability = 0
            print("Still full...")
        else:
            print("Bookings Available!!", availability)
            contents = common.load_file(glbs.LOG_DIR + "/cron.log")
            if "Bookings Available!!" in contents:
                raise Exception("Email already sent")
            port = 465  # For SSL
            # Create a secure SSL context
            context = ssl.create_default_context()
            sender_email = "xpokefirex@gmail.com"
            sender_password = "baabaa123"
            receiver_email = "pokefire.seasons@gmail.com"
            receiver_email2 = "marie-soulodre@hotmail.com"
            booking_link = "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=3b34573ebf36421fb31011f8dc557032&random=5fe40b282c590&iframeid=&mode=p"
            message = f"""\
            Subject: Altitude Booking is Available!!!!

Hey,\n\n There are {availability} spots available at Altitude for {time_slot}. \n You can book here: {booking_link} \n\n Cheers, Peter"""
            with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, message)
                server.sendmail(sender_email, receiver_email2, message)

            print("Email sent to : {sender_email}")
        return None
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
        # Variables
        locations = {'Altitude Kanata': {'url': 'https://app.rockgympro.com/b/widget/?a=offering&offering_guid=90a6abd5e5124f7384b2b60d00683e3d&random=5f1483d0c152d&iframeid=&mode=p',
                                         'capacity': 50}}
        name = 'Altitude Kanata'
        driver = get_driver()

        get_bookings(
            driver, name, locations[name]['capacity'], locations[name]['url'])
        driver.quit()
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        # print(ex)
        raise ex
