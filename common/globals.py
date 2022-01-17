"""This module contains global variables used by various scripts within this project."""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import config  # noqa

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCKER_DIR = os.path.join(BASE_DIR, "docker")
CLI_DOCKER_DIR = os.path.join(DOCKER_DIR, "cli")
WEB_SCRAPER_DOCKER_DIR = os.path.join(DOCKER_DIR, "webscraper")
LOG_DIR = os.path.join(BASE_DIR, "logs")
CLI_LOG_DIR = os.path.join(LOG_DIR, "cli")
WEB_SCRAPER_LOG_DIR = os.path.join(LOG_DIR, "webscraper")
IMAGE_LOG_DIR = os.path.join(LOG_DIR, "images")
COMMON_DIR = os.path.join(BASE_DIR, "common")
WEB_SCRAPER_DIR = os.path.join(BASE_DIR, "web_scraper")
WEB_SCRAPER_ENV_DIR = os.path.join(WEB_SCRAPER_DIR, "env")
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_DIR = os.path.join(DATA_DIR, "input")
EMAIL_TEMPLATE_DIR = os.path.join(DATA_DIR, "email_templates")
TEMPLATE_DIR = os.path.join(INPUT_DIR, "templates")
SAMPLE_DATA_DIR = os.path.join(TEMPLATE_DIR, "sample_data")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
TREND_DIR = os.path.join(DATA_DIR, "trend_analysis")
IMAGE_DIR = os.path.join(BASE_DIR, "images")
NOTEBOOK_DIR = os.path.join(IMAGE_DIR, "notebook")
# Create directories not tracked by git
if not os.path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)
if not os.path.exists(CLI_LOG_DIR):
    os.mkdir(CLI_LOG_DIR)
if not os.path.exists(WEB_SCRAPER_LOG_DIR):
    os.mkdir(WEB_SCRAPER_LOG_DIR)
    with open("cron.log", "w") as f:
        pass
if not os.path.exists(IMAGE_LOG_DIR):
    os.mkdir(IMAGE_LOG_DIR)

# Elasticsearch
ES_URL = "http://localhost:9200"
ES_URL_DOCKER = "http://host.docker.internal:9200"
ES_DIR = os.path.join(DATA_DIR, "elasticsearch")
ES_MAPPINGS = os.path.join(ES_DIR, "mappings")
ES_INDEX_NAME = ["bookings", "sessions", "counters", "projects"]
ES_BULK_DATA = os.path.join(ES_DIR, "bulk_data")
# Kibana
KIBANA_URL = "http://localhost:5601"
KIBANA_URL_DOCKER = "http://host.docker.internal:5601"
# Weather data
WEATHER_DIR = os.path.join(DATA_DIR, "weather")
OTTAWA_WEATHER = os.path.join(WEATHER_DIR, "ottawa_weather.csv")
GATINEAU_WEATHER = os.path.join(WEATHER_DIR, "gatineau_weather.csv")
WEATHER_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/history"  # noqa
# Generated ENV File
BOOKINGS_ENV = os.path.join(WEB_SCRAPER_DOCKER_DIR, "bookings.env")
# Paths to default templates for climbing logs

_altitude_kanata = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_altitude_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "indoor_bouldering_altitude_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_altitude_kanata.yaml")
)
_altitude_gatineau = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_altitude_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "indoor_bouldering_altitude_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_altitude_gatineau.yaml")
)
_coyote_rock_gym = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_coyote_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "indoor_bouldering_coyote_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_coyote.yaml")
)
_klimat = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_klimat_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "indoor_bouldering_klimat_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_klimat.yaml")
)
_calabogie = (
    os.path.join(TEMPLATE_DIR, "outdoor_bouldering_calabogie_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "outdoor_bouldering_calabogie_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "outdoor_bouldering_calabogie.yaml")
)
_up_the_bloc = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_up_the_bloc_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "indoor_bouldering_up_the_bloc_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_up_the_bloc.yaml")
)
_cafe_bloc = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_cafe_bloc_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "indoor_bouldering_cafe_bloc_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_cafe_bloc.yaml")
)
_allez_up = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_allez_up_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "indoor_bouldering_allez_up_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_allez_up.yaml")
)
_bloc_shop_chabanel = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_bloc_shop_chabanel_personal.yaml")
    if os.path.exists(
        os.path.join(TEMPLATE_DIR, "indoor_bouldering_bloc_shop_chabanel_personal.yaml")
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_bloc_shop_chabanel.yaml")
)
_bloc_shop_hochelaga = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_bloc_shop_hochelaga_personal.yaml")
    if os.path.exists(
        os.path.join(
            TEMPLATE_DIR, "indoor_bouldering_bloc_shop_hochelaga_personal.yaml"
        )
    )
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering_bloc_shop_hochelaga.yaml")
)
_hogs_back = (
    os.path.join(TEMPLATE_DIR, "outdoor_bouldering_personal.yaml")
    if os.path.exists(os.path.join(TEMPLATE_DIR, "outdoor_bouldering_personal.yaml"))
    else os.path.join(TEMPLATE_DIR, "outdoor_bouldering.yaml")
)
_default = (
    os.path.join(TEMPLATE_DIR, "indoor_bouldering_personal.yaml")
    if os.path.exists(os.path.join(TEMPLATE_DIR, "indoor_bouldering_personal.yaml"))
    else os.path.join(TEMPLATE_DIR, "indoor_bouldering.yaml")
)
_default = _altitude_kanata
GYM_TEMPLATE = {
    "kanata": _altitude_kanata,
    "altitude kanata": _altitude_kanata,
    "gatineau": _altitude_gatineau,
    "altitude gatineau": _altitude_gatineau,
    "coyote": _coyote_rock_gym,
    "coyote rock gym": _coyote_rock_gym,
    "klimat": _klimat,
    "calabogie": _calabogie,
    "up the bloc": _up_the_bloc,
    "hogs back": _hogs_back,
    "hog's back": _hogs_back,
    "cafe bloc": _cafe_bloc,
    "allez up": _allez_up,
    "bloc shop chabanel": _bloc_shop_chabanel,
    "bloc shop hochelaga": _bloc_shop_hochelaga,
    "default": _default,
}

if config.default_gym:
    default = config.default_gym.lower()
if isinstance(default, str) and default in GYM_TEMPLATE.keys():
    GYM_TEMPLATE.update({"default": GYM_TEMPLATE[default]})
