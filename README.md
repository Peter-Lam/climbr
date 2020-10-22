[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url]
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/peter-lam/climbr/blob/master/LICENSE)

<br />
<p align="center">
  <h1 align="center">Climbr</h1>
  <a>
    <img src="images\trends\trends_dash.png" alt="climbr dashboard dmeo">
  </a>
  <p align="center">
    Visualize your rock climbing progression and trends. 
    <br />
    <a href="https://github.com/Peter-Lam/climbr"> Website</a>
        ·
    <a href="https://github.com/Peter-Lam/climbr/wiki">Wiki</a>
    ·
    <a href="https://github.com/Peter-Lam/climbr/issues">Report Bug</a>
    ·
    <a href="https://github.com/Peter-Lam/climbr/issues">Request Feature</a>
  </p>
</p>

# About
**`Climbr`** is a utility that allows users to visualize and highlight their climbing strengths, weaknesses, and trends. From professionals to beginners, trad climbers to indoor boulderers, users can log climbing sessions from a selection of templates and instantly view their trends, patterns, and statistics with pre-configured Kibana dashboards.

In addition, **`Climbr`** provides booking insights on local gyms (Altitude Kanata, Altitude Gatineau, Coyote Rock Gym), to help users find the most optimal climbing time according to location, time of day, and time of week. Climbers can utilize this information to make socially responsible decisions. Those looking to minimize their risk whilst still staying active can easily find the off-peak hours of their local gym. 

## Technologies
<p float="left">
  <a href="https://www.python.org/">
    <img src="images\misc\python.png" alt="python logo" width="100">
  </a>
  <a href="https://www.docker.com/">
  <img src="images\misc\docker.png" alt="docker logo" width="100">
  </a>
  <a href="https://www.elastic.co/">
  <img src="images\misc\elasticsearch.png" alt="elastic logo" width="100">
  </a>
  <a href="https://www.elastic.co/kibana">
  <img src="images\misc\kibana.png" alt="kibana logo" width="100">
  </a>
</p>

## Contributors
### Peter Lam
  - [Website](peterqlam.com)
  - [Linkedin](https://www.linkedin.com/in/peter-lam-612a00138/)
  - [Resume](https://www.peterqlam.com/s/Peter-Lam-Resume.pdf)
# Features

- Log your climbing sessions and projects using yaml files
- Visualize climbing trends, patterns, and statistics with dashboards
  - Climbing Stats and Metrics
    - Map of visited locations
    - Most common climbing discipline (Lead, Bouldering, Trad)
    - Grade counter
  - Climbing Trends and Progression
    - Progression in grades over time
    - What's your flash grade? project grade?
    - Strongest/Weakest climbing style? What areas should I improve?
    -
  - Bookings
    - Busiest time to climb
    - Best time to climb to avoid crowds
    - Average bookings based on gym
- Use data to influence your training regime and pinpoint weaknesses
- Make responsible decisions based on booking data


# Host Requirements
- [Docker 19+](https://www.docker.com/products/docker-desktop)
- Python 3.6+ (Optional)
  - Linux: `sudo apt-get install python3 && python3 -m pip install -U pip`
  - [Windows:](https://www.python.org/downloads/) Ensure *'Add Python to PATH'* is selected

**Note**: Climbr can be run without Docker.
The following must be running on your host machine:
 - [ElasticSearch 7.9.2](https://www.elastic.co/downloads/elasticsearch)
 - [Kibana 7.9.2](https://www.elastic.co/downloads/kibana)
 - [Python 3.6+](https://www.python.org/downloads/) 
# Quick Start
## Climbr
1. Open Command Prompt/Terminal
2. Change directories to this the root of this repository
3. Build and start up ElasticSearch, Kibana, and Climbr containers with:
    ```shell
    docker-compose up -d --build
    ```
    **Note:** This process may take a while to build
4. Confirm that all containers are running
    - Run `docker ps`, the containers *climbr_cli*, *climbr_kibana*, and *climbr_es* should be running
    - You should be able to establish a connection to http://localhost:5601
    - If the link is not reachable, wait a couple minutes and try again
5. Run the demo visualizations and data
    - If python is installed:  
      1. Run the command `python ./climbr.py demo`
    - Otherwise:
      1. Copy the `CONTAINER ID` into your clipboard for the docker container of name `climber_cli`
      2. Run the following command to initialize the demo
          ```shell
          docker exec <CONTAINER_ID> bash -c "python ./climbr.py demo" 
          ```
6. View Climbr visualizations at: http://localhost:5601/app/dashboard
## Bookings
1. Open Command Prompt/Terminal
2. Change directories `<PATH_TO_REPO>/web_scraper`
3. Run webscraper
    - Automated: start up bookings container by running
      ```shell
      docker-compose up -d --build
      ```
      **Note:** Confirm that the container `climbr_bookings` is running with the command `docker ps`
    - Manually: with Python
      ```shell
      python bookings.py ./bookings.py -l Altitude_Gatineau
      ```
4. View Climbr visualizations at: http://localhost:5601/app/dashboard

# Getting Started
Please visit the [wiki](https://github.com/Peter-Lam/climbr/wiki) for more information regarding system requirements, set-up, and usage.


[contributors-shield]: https://img.shields.io/github/contributors/peter-lam/climbr.svg?style=flat-square
[contributors-url]: https://github.com/peter-lam/climbr/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/peter-lam/climbr.svg?style=flat-square
[forks-url]: https://github.com/peter-lam/climbr/network/members
[stars-shield]: https://img.shields.io/github/stars/peter-lam/climbr.svg?style=flat-square
[stars-url]: https://github.com/peter-lam/climbr/stargazers
[issues-shield]: https://img.shields.io/github/issues/peter-lam/climbr.svg?style=flat-square
[issues-url]: https://github.com/peter-lam/climbr/issues
[license-shield]: https://img.shields.io/github/license/peter-lam/climbr/.svg?style=flat-square
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/peter-lam-612a00138/