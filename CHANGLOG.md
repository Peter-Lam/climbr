# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [4.1.1] [2022-01-15] Minor logging fixes

### Changed

- log level of webscraper
- crontab (note as of Jan 14th, all local gyms are closed again)

### Fixed

- log output format for weather.py

## [4.1.0] [2022-01-02] Webscraper directory clean up

### Changed

- script and file locations for webscraper
- log level for weather data from INFO to DEBUG
- log folder locations
- export message to display the output path

## [4.0.0] [2022-01-01] Added logging and fixed email notifications

### Added

- loguru to log all python files (Resolves #21 and #24)
  - climbr.py -> climbr.log
  - bookings.py -> webscraper.log (monthly file rotation)
  - cron.log (for system out of webscraper)
- callback functions to send email notificaion upon error
- warning when number of reservations is greater than capacirt (#41)

### Fixed

- Error notification when using crontab
- Error notification attachment to display filename

### Removed

- Removed redundant try & except statements
- Replaced silent option in existing functions with log levels. If -q is selected, log level will only show errors

## [3.4.1] [2021-12-27] Updated webscraper for Altitude Capacity

### Changed

- cron job to check Altitude Gatineu for capacity every 30mins

### Fixed

- Zone labeling for Altitude Gatineau
- Retroactively changed capacity for Annex, should have been 25max not 20. 

## [3.4.0] [2021-12-24] Updated webscraper for Altitude Zones

### Added

- startup.bat to quickly start the webscraper
- weather command to update FireStore weather in pyproject.toml
- new weather and bookings data

### Changed

- bookings.py and crontab to account for Gatineau's Zone system
- crontab with updated times

## [3.3.0] [2021-12-19] Updated webscraper for Altitude and Coyote

### Changed

- bookings.py and crontab to account for reservation and capaicty limits in Ottawa/Gat

### Fixed

- Variable assignment in session.py

### Removed

- Unused print statement in globals.py

## [3.2.1] [2021-11-15] Added templates for Allez Up and Bloc Shop

### Added

- Template support for Allez Up, Bloc Shop Hochelaga, and Bloc Shop Chabanel
- Latest bookings and weather data

### Changed

- Template logic to fill content based on config.py (list of climbers and shoes)

### Fixed

- Yaml files now accpet list and str values for "Shoes"

## [3.2.0] [2021-10-31] Added more data for visualizations

### Added

- end_hour and end_minute to allow for detailed time ranges in Kibana
- percent_full to old data

## [3.1.1] [2021-10-30] Fixed deprecation warning, and poetry dependencies

### Fixed

- Deprecation warning in bookings.py

### Removed

- (#36) pyproject.toml and poetry.lock files from /webscraper. Using entrypoint.sh to source the parent files instead

## [3.1.0] [2021-10-29] Updated webscraper for Gatineau and added Poetry to docker

### Changed

- bookings.py to check a new url for the gatineau location
- crontab to check every 30 mins from 9 AM - 10:40
- dockerfile to use poetry instead of pip install

### Fixed

- Bug with starting a webscraper container without the cron.log file

## [3.0.7] [2021-10-28] Fixed linting issues

### Fixed

- linting for:
    - .\web_scraper\
    - .\common\
    - config.py
    - noxfile.py

## [3.0.6] [2021-10-28] Updated weather and bookings data

### Changed

- bookings.json and weather csv's to included latest data since Altitude and Coyote are no longer doing reservations

## [3.0.5] [2021-10-25] #31 Create missing untracked folders

### Fixed

- globals.py to create "logs" and "output" folders if ti doesn't exist in the project

## [3.0.4] [2021-10-22] #29 Adding Poetry and Nox

### Added

- pyproject.toml for installing dependencies for Poetry
- noxfile.py for running nox linters and safety checks

### Changed

- All python files to comply with flake8 linting standards
- climbr.py by separating commands into their own functions

## [3.0.3] [2021-10-24] Updated Crontab & Webscraper for October 25

### Changed

- crontab to removed coyote rock gym times since they will no longer use a reservation system
- bookings.py to increase Altitude Kanata capacity to 250

## [3.0.2] [2021-10-17] Bugfix: reduced logging output

### Changed

- bookings.py to output fell exception only when it doesn't contain: "no such index [bookings]" to reduce the 5k line log output

## [3.0.1] [2021-10-03] Bugfix: Webscraper container would not start

### Fixed

- Entrypoint in dockerfile with the correct params

### Removed

- pylint workflow - will evaluate best linter for this project and re-implement

## [3.0.0] [2021-03-19] Updated web scraper for local gyms

### Added 
- restart scripts for quick reboot of webscraper docker containers

### Changed
- Updated cron times for gyms, capacity changes and new data for updated covid guidelines

----

## [2.0.0] [2021-09-23] New log option and email notification support

### Added
- New option to create log from template via command line
    - Supporting: Altitude Kanata, Altitude Gatineau, Coyote Rock Gym, Klimat, Up the Bloc, Cafe Bloc, Calabogie, Hog's back
- Support for email notifications in an event of an error
- Email template for notifications
- An updated version of local weather and booking data

### Changed
- Cron jobs to reflect re-opening of gyms and new regulations
- Climbing templates to have "experience" field, and fixed some minor mistakes to grading and values

### Fixed
- Entering multiple shoes with ',' and '/' will now separate into multiple shoes
- When entering multiple climbing styles, each style is now stripped on whitespace
- Counters are no longer a requirement in climbing logs (allows for logging visits or hangout days)
- Corrected the path thats displayed to user when uploading to Kibana 

----

## [1.3.0] [2021-03-19] Updated web scraper for local gyms

### Changed
- booking.py to work with local gyms transitioning to red zone

## [1.2.1] [2021-03-10] Updated historical data and web scraper cron jobs

### Added
- Updated local weather and booking data

### Changed
- CRON to reflect local gym hours
- Web scraper to reflect Gatineau changes

## [1.2.0] [2020-12-11] Google Firestore support added

### Added
- Updated local weather and booking data

### Changed
- requirements.txt file for firebase_admin dependancu
- config.py to add an option for Firestore connections
- common.py to add a firestore connection function

## [1.1.0] [2020-12-05] Added Jupyter Notebook with corresponding scripts to gather weather data
 Python Notebook added, Weather is now being tracked, and booking crontab has been updated to reflect recent Coyote time changes

### Added

- weather.py to gather weather data for Kanata and Gatineau
- Python notebook to analyze online booking trends associated with weather
- Python notebook to analyze common words within session logs
- Weather data stored in csv for Gatineau and Kanata
- New sample images from notebook
- Config file for API key for https://www.visualcrossing.com/

### Changed

- crontab with new booking times and scheduled API calls for weather
- bookings.json with more data
- requirements.txt

### Fixed

- Templates had 'V5/6' instead of 'V5/V6'

## [1.0.1] [2020-11-06] Web scraper updated

### Added

- New bookings data

### Changed

- crontab to track Altitude Kanata, and Coyote (reopens Oct 7th)
- Docker-compse now auto restarts when closed 
