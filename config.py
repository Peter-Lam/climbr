import os

import common.common as common
import common.globals as glbs

# API key for https://www.visualcrossing.com/
# Used for weather data on bookings
# Can be left empty if features are not needed
weather_key = ''
firestore_json = ''
# Email credentials used to send SMTP requests when errors occur. Uses ENV variables
# Can be left empty if email notification is not needed
smpt_email = os.getenv('CLIMBR_EMAIL')
smpt_pass = os.getenv('CLIMBR_PASS')

# Email to send notifications to
to_notify = ''

# Home gym
home_gym = ''
