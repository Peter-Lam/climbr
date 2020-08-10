# bookings.py
`bookings.py` collects Altitude Gym's availability for a current climbing session. Although this script can be manually ran, `/crontab` has been provided to automatically call this script 2 minutes before the end of a session.

## Motivation
Looking for trends in the session availability so I can plan my climbing days accordingly. With COVID-19, I'm looking to climb when the gym is most likely to be empty

Questions looking to answer through data collection:
- When is the gym most busy? least?
- Is it typically emptier on weekends?
- Night vs morning climbs?
- How does weather influence general bookings? Do more people climb when it's nice out?

## Prerequisites
- [Python 3.6+](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/products/docker-desktop) (Required for automated method)
- Chrome 84.0.4147 (Required for manual method)

## Getting Started
### Manual Method
1. In command-line/terminal, change directories to Climbing-Tracker/web_scraper/
    ```
    cd Climbing-Tracker/web_scraper/
    ```
2. To run the script, type the following
    ```
    python bookings.py
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