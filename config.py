"""User configurable settings."""

import os

# API key for https://www.visualcrossing.com/
# Used for weather data on bookings
# Can be left empty if features are not needed
weather_key = ""
firestore_json = ""
# Email credentials used to send SMTP requests when errors occur. Uses ENV variables
# Can be left empty if email notification is not needed
smpt_email = os.getenv("CLIMBR_EMAIL")
smpt_pass = os.getenv("CLIMBR_PASS")

# Email to send notifications to
to_notify = ""

# User configurable template information
default_gym = ""
shoes = ["Shoes_Here", "Shoes_Here"]
climbers = ["Climber A", "Climber B"]
