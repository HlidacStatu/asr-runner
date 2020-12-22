#!/usr/bin/env python
import requests
import os
import json
import logging
import time
import shutil
import uuid

from ftps import Ftps
from config import CONFIG as cfg

queue = cfg['QUEUE']['TASK_QUEUE']
success = cfg['QUEUE']['REPORT_SUCCESS']
failure = cfg['QUEUE']['REPORT_FAILURE']
headers = cfg['QUEUE']['HEADERS']
wait = cfg['RUN']['WAIT_SECONDS']
local_folder = cfg['RUN']['LOCAL_FOLDER']
test_phase = cfg['RUN']['TEST_PHASE']


def docker_installed():
    logging.debug('Checking if docker is installed')
    output = False
    if test_phase: return True

    cmd = 'docker image ls | grep hlidacstatu/czech-asr | grep latest-stable'
    rc = os.system(cmd)
    if rc == 0: output = True

    return output


def run_conversion():
    logging.debug('Running conversion')
    if test_phase: return random.getrandbits(1)
    cmd = 'docker run --rm -v ' + temp_folder + ':/opt/app/files -e NUM_JOBS=1 -e DECODE_NUM_JOBS=1 -e DECODE_NUM_THREADS=4 hlidacstatu/czech-asr:latest-stable'
    logging.debug('Command ->[' + cmd + ']<-')

    return os.system(cmd)


def run_script(param):
    # check existence of a script from config
    if not os.path.isfile(video_script):
        logging.info('Script ->[' + video_script + ']<- not found')
        return False

    # run
    cmd = video_script + ' ' + param

    return os.system(cmd)


def read_queue():
    if test_phase:
        logging.info('Testing ...')
        output = {
            "dataset": "",
            "itemid": "honzatest"
        }
        return output
    response = requests.request('GET', queue, headers=headers)
    if response.status_code == 200:
        logging.info('Status OK')
        logging.debug('Response: ' + response.text)
        output = json.loads(response.text)
    else:
        logging.info('Something went wrong or empty queue: ' + response.reason)
        output = False

    return output


def cleanup(folder):
    logging.debug('Cleaning up folder ->[' + folder + ']<-')
    try:
        shutil.rmtree(folder)
    except:
        logging.error('Could not remove folder ->[' + folder + ']<-')


def report_success(data):
    logging.info('Task finished successfully')
    if test_phase:
        cleanup(temp_folder)
        exit(0)

    response = requests.request('POST', success, headers=headers, data=data)
    if response.status_code == 200:
        logging.info('Success reported')
    else:
        logging.info('Could not report succeeded task: ' + response.reason)
    cleanup(temp_folder)


def report_failure(data):
    logging.info('Task failed')
    if test_phase:
        cleanup(temp_folder)
        exit(0)

    response = requests.request('POST', failure, headers=headers, data=data)
    if response.status_code == 200:
        logging.info('Failure reported')
    else:
        logging.info('Could not report failed task: ' + response.reason)
    cleanup(temp_folder)


################
# Main program #
################

# logging.basicConfig(filename='main.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

# run an infinite loop
while True:
    # check if docker image docker hlidacstatu/czech-asr:latest-stable is present
    if not docker_installed():
        logging.error('Could not find docker image for voice2text conversion')
        time.sleep(600)
        continue

    task = read_queue()
    if task:
        logging.info('Task available, running video processing script')
        logging.debug('Task info: ' + task.__str__())

        # get arguments for the video processing script
        arg = task['dataset'] + ' ' + task['itemid']
        remote_folder = task['dataset']
        filename = task['itemid']

        # create temporary folder to store downloaded and coverted files
        temp_folder = local_folder.rstrip('/') + '/' + uuid.uuid4().__str__()
        logging.debug('Temporary local folder: ' + temp_folder)
        os.makedirs(temp_folder)
        # os.chdir(temp_folder)

        # connect to ftp and download file
        logging.info('Trying to download file ' + filename)
        ftp_client = Ftps()
        result = ftp_client.download(filename, temp_folder, remote_folder)

        if result:
            rc = run_conversion()
            if rc == 0:
                logging.info('Conversion run successfully')

                # copy test file
                output_file = filename + ftp_client.output_format
                if test_phase: shutil.copy('/var/tmp/' + output_file, temp_folder)

                # get the size of the converted file for comparison
                logging.debug('Get local file size')
                local_file_path = local_folder.rstrip('/') + '/' + output_file
                local_file_size = os.path.getsize(local_file_path)
                logging.debug('Local file size is: ' + str(local_file_size))

                # upload the converted file
                ftp_client.upload(output_file, local_folder, remote_folder)
                # remote_file_path = '/' + remote_folder.strip('/') + filename + ftp_client.output_format
                ftp_file_size = ftp_client.size(output_file, remote_folder)
                if int(local_file_size) == int(ftp_file_size):
                    logging.info('Converted file uploaded successfully')
                    report_success(task)
                else:
                    logging.error('Could not upload converted file')
                    report_failure(task)
            else:
                report_failure(task)
    else:
        time.sleep(wait)
