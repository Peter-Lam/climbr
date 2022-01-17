#!/bin/bash
# A startup script for the webscraper container 
# Intializes cron jobs and passes enviroment variable for container to crontab
echo "Starting container: climbr_bookings"
env > ../docker/webscraper/bookings.env
chmod +x ../docker/webscraper/bookings.env
printenv | grep -v "no_proxy" >> /etc/environment
# poetry config virtualenvs.create false
poetry install --no-interaction --no-ansi
cron && tail -f /workspace/logs/webscraper/cron.log
echo "Container sucefully started: climbr_bookings"
