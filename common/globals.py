'''
This module contains global variables used by various scripts within this project
'''
import os
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
COMMON_DIR = os.path.join(BASE_DIR, 'common')
WEB_SCRAPER_DIR = os.path.join(BASE_DIR, 'web_scraper')
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_DIR = os.path.join(DATA_DIR, 'input')
SAMPLE_DATA_DIR = os.path.join(INPUT_DIR, 'templates', 'sample_data')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
# Elasticsearch
ES_URL = "http://localhost:9200"
ES_DIR = os.path.join(DATA_DIR, 'elasticsearch')
# Kibana
KIBANA_URL = "http://localhost:5601"
