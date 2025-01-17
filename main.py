# Stub out some common entry points to later convert to tests after everything is wired up together

import logging
import time
import os
import yaml
import sys

from model import aircraft_report
from model import report_receiver
from utils import postgres as pg_utils

# set some defaults
config = {
    'feed1': {'url': ''},
    'receiver1': {'lat83': '', 'long83': ''},
    'feed2': {'url': ''},
    'receiver2': {'lat83': '', 'long83': ''}, 
    'database': {'hostname': '', 'port': 5432, 'dbname': '', 'user': '', 'pwd': ''},
    'waittimesec': 5,
    'samplescutoff': 100000000,
    'itinerarymaxtimediffseconds': 900,
}
   
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yml')
if os.path.exists(config_path): 
    with open(config_path) as yaml_config_file:
        config = yaml.load(yaml_config_file)

# log_formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(name)s - %(process)s - %(message)s")
FORMAT = '%(asctime)-15s %(levelname)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)

# config vars, let environment variables overrule even if there is a config file
aircraft_data_url1 = os.environ.get('FEED1_URL', config['feed1']['url'])
receiver1_lat83 = os.environ.get('RECEIVER1_LAT', config['receiver1']['lat83'])
receiver1_long83 = os.environ.get('RECEIVER1_LONG', config['receiver1']['long83'])

aircraft_data_url2 = os.environ.get('FEED2_URL', config['feed2']['url'])
receiver2_lat83 = os.environ.get('RECEIVER2_LAT', config['receiver2']['lat83'])
receiver2_long83 = os.environ.get('RECEIVER2_LONG', config['receiver2']['long83'])

db_hostname = os.environ.get('DB_HOST', config['database']['hostname'])
db_port = os.environ.get('DB_PORT', config['database']['port'])
db_name = os.environ.get('DB_NAME', config['database']['dbname'])
db_user = os.environ.get('DB_USER', config['database']['user'])
db_pwd = os.environ.get('DB_PASSWD', config['database']['pwd'])

sleep_time_sec = config['waittimesec']

total_samples_cutoff_val = config['samplescutoff']

postgres_db_connection = pg_utils.database_connection(dbname=db_name,
                                                      dbhost=db_hostname,
                                                      dbport=db_port,
                                                      dbuser=db_user,
                                                      dbpasswd=db_pwd)

radio_receiver_1 = report_receiver.RadioReceiver(name='piaware1',
                                                 type='raspi',
                                                 lat83=receiver1_lat83,
                                                 long83=receiver1_long83,
                                                 data_access_url='',
                                                 location="")

radio_receiver_2 = report_receiver.RadioReceiver(name='piaware2',
                                                 type='raspi',
                                                 lat83=receiver2_lat83,
                                                 long83=receiver2_long83,
                                                 data_access_url='',
                                                 location="")


def harvest_aircraft_json_from_pi():
    logger.info('Aircraft ingest beginning.')
    total_samples_count = 0
    failure_num = 0
    while total_samples_count < total_samples_cutoff_val:
        try:
            start_time = time.time()

            current_reports_list = aircraft_report.get_aircraft_data_from_url(aircraft_data_url1)
            if len(current_reports_list) > 0:
                aircraft_report.load_aircraft_reports_list_into_db(
                    aircraft_reports_list=current_reports_list,
                    radio_receiver=radio_receiver_1,
                    dbconn=postgres_db_connection)

            end_time = time.time()
            logger.debug('{} seconds for data pull from Pi'.format((end_time - start_time)))
            total_samples_count += 1
            time.sleep(sleep_time_sec)
        except:
            # Workaround for failing connection when pi gets busy
            logger.exception('Issue getting data from a receiver {}'.format(radio_receiver_1))
            time.sleep(120)
            failure_num += 1
            if failure_num > 10:
                exit(1)



if __name__ == '__main__':
    logger.debug('Entry from main.py main started')
    harvest_aircraft_json_from_pi()
