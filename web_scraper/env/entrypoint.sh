#!/bin/bash
# A startup script for the webscraper container 
# Intializes cron jobs and passes enviroment variable for container to crontab
echo "Webscraper container has started"
env > ./env/bookings.env
chmod +x ./env/bookings.env
printenv | grep -v "no_proxy" >> /etc/environment
# poetry config virtualenvs.create false
poetry install --no-interaction --no-ansi
# cron already running from dockerfile
# Setup cron job
cron && tail -f /workspace/logs/webscraper/cron.log