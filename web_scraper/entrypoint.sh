#!/bin/bash
# A startup script for the webscraper container 
# Intializes cron jobs and passes enviroment variable for container to crontab
echo "Webscraper container has started"
env > bookings.env
chmod +x bookings.env
# cron already running from dockerfile
# Setup cron job
cron && tail -f /workspace/logs/cron.log