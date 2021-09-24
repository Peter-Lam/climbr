#!/bin/bash

# Restarting docker containers for webscraper
docker-compose down
docker-compose up -d --build