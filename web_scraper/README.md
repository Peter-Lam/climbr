# bookings.py
`bookings.py` collects the availability for a current climbing session. Although this script can be manually ran, a crontab has been provided to automatically call this script 2 minutes before the start of a session. This script currently collects booking data from Altitude Kanata, Altitude Gatineau, and Coyote Rock Gym

## Motivation
Looking for trends in the session availability so I can plan my climbing days accordingly. With COVID-19, I'm looking to climb when the gym is most likely to be empty

Questions looking to answer through data collection:
- When is the gym most busy? least?
- Is it typically emptier on weekends?
- Night vs morning climbs?
- How does weather influence general bookings? Do more people climb when it's nice out?
- How do bookings compare across gyms locations?

## Prerequisites
- [Python 3.6+](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/products/docker-desktop) (Required for automated method)
- Chrome 84.0.4147 (Required for manual method)

## Getting Started
### Usage
```
usage: bookings.py [-h] [--version] -l locations) [location(s ...]

Utility for gathering booking data from climbing gyms

optional arguments:
  -h, --help                        show this help message and exit
  -l location(s) [location(s) ...]  Climbing Gym locations [Altitude_Kanata, Altitude_Gatineau, Coyote_Rock_Gym]

General Options:
  --version                         show program's version number and exit
```

Currently supported locations (Can pick multiple):
- Altitude_Kanata
- Altitude_Gatineau
- Coyote_Rock_Gym

### Manual Example
1. In command-line/terminal, change directories to Climbing-Tracker/web_scraper/
    ```
    cd Climbing-Tracker/web_scraper/
    ```
2. To run the script, type the following
    ```
    python bookings.py -l Altitude_Kanata
    ```
3. Information will be stored in `Climbing-Tracker/output/bookings.json` which can be uploaded to Elasticsearch with the main project script and the command:,
    ```
    climb.py update
    ```

### Automated Method
**Note:** You must have docker installed for this method, see [Prerequisites](##Prerequisites)

1. In command-line/terminal, change directories to Climbing-Tracker
    ```
    cd Climbing-Tracker/
    ```
2. Then run the following command to create the docker container
    ```
    docker-compose up -d
    ```