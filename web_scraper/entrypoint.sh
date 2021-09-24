#!/bin/bash

# A startup script for the webscraper container 
# Intializes cron jobs and passes enviroment variable for container to crontab
echo "Webscraper container has started"
env > /workspace/web_scraper/bookings.env
chmod +x /workspace/web_scraper/bookings.env
# cron already running from dockerfile
# Setup cron job
cron && tail -f /workspace/logs/cron.log