# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] New log option and email notification support

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

# Fixed
- Templates had 'V5/6' instead of 'V5/V6'

## [1.0.1] [2020-11-06] Web scraper updated

### Added 
- New bookings data

### Changed
- crontab to track Altitude Kanata, and Coyote (reopens Oct 7th)
- Docker-compse now auto restarts when closed 