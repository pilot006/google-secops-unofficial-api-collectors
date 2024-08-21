from SiemplifyJob import SiemplifyJob
import google.auth.transport.requests
from google.oauth2 import service_account
import json
import requests
import re
from datetime import datetime, timedelta
import CollectorUtils


INTEGRATION_NAME = "Unofficial SecOps API Collectors"
SCRIPT_NAME = "1Password - Events"

siemplify = SiemplifyJob()
siemplify.script_name = SCRIPT_NAME

# INIT INTEGRATION CONFIGURATION:
BEARER = siemplify.extract_job_param(param_name="1Password Bearer Token", print_value=False)
API_URL = siemplify.extract_job_param(param_name="1Password Base URL", print_value=True)
TIME_INTERVAL = siemplify.extract_job_param(param_name="Job interval (minutes)", print_value=True)
INGESTION_SA_JSON = siemplify.extract_job_param(param_name="SecOps Ingestion API v2 JSON", print_value=False)
INGESTION_SA_JSON = json.loads(INGESTION_SA_JSON)
CUSTOMER_ID = siemplify.extract_job_param(param_name="SecOps Customer ID", print_value=False)

# Log types: https://cloud.google.com/chronicle/docs/ingestion/parser-list/supported-default-parsers
LOG_TYPE = "ONEPASSOWRD"
log_batch = []

def main():

    try:
        
        cursor = None
        cursor = get_onepassword_events(cursor)
        while cursor != None:
            cursor = get_onepassword_events(cursor)

        # If we still have logs in the batch, send them now that we're at the end
        if log_batch != []:
            siemplify.LOGGER.info('Sending non-full batch at end.')
            c = CollectorUtils.secops.upload(INGESTION_SA_JSON, 
                                            CUSTOMER_ID,
                                            LOG_TYPE,
                                            log_batch
                                            )
            siemplify.LOGGER.info('SecOps API response: ' + c)

    except Exception as e:
        siemplify.LOGGER.error("General error performing Job {}".format(SCRIPT_NAME))
        siemplify.LOGGER.exception(e)
        raise

    siemplify.end_script()

def get_onepassword_events(cursor):
    headers = {
        "Accept":         "application/json",
        "Content-Type":   "applicaiton/json",
        "Authorization":  "Bearer " + BEARER
    }

    d = datetime.now() - timedelta(hours=0, minutes=int(TIME_INTERVAL))
    start_time = d.strftime('%Y-%m-%dT%H:%M:00.0Z')
    e = datetime.now() - timedelta(hours=0, minutes=1)
    end_time = e.strftime('%Y-%m-%dT%H:%M:59.99999Z')
    siemplify.LOGGER.info("start_time: " + start_time)
    siemplify.LOGGER.info("end_time: " + end_time)

    if cursor == None:
        payload = {
            "limit": 1000,
            "start_time": start_time,
            "end_time" : end_time
        }
    else:
        payload = {
            "cursor": cursor
        }

    # https://developer.1password.com/docs/events-api/reference/#post-apiv1auditevents
    url = API_URL + "/api/v1/auditevents"
    req = requests.post(url=url,headers=headers, json=payload)
    siemplify.LOGGER.info("1Password API Response: " + req.text)
    js = json.loads(req.text)
    if 'cursor' and 'has_more' in js:
        siemplify.LOGGER.info('cursor detected: ' + js['cursor'])
        for i in js['items']:
            siemplify.LOGGER.info(i)
            batch_logs(i)
        if js['has_more'] == False:
            return None
        else:
            return js['cursor']
    else:
        for i in js['items']:
            batch_logs(i)
        return None

def batch_logs(log_line):
    batch_size = len(json.dumps(log_batch).encode())
    siemplify.LOGGER.info('Batch size: ' + str(batch_size))
    # Batch size is limited to 1 MB: https://cloud.google.com/chronicle/docs/reference/ingestion-api#unstructuredlogentries
    if batch_size < 800000:
        entry = { "log_text": json.dumps(log_line) }
        log_batch.append(entry)
        #siemplify.LOGGER.info(json.dumps(log_batch, indent=1))
    else:
        entry = { "log_text": json.dumps(log_line) }
        log_batch.append(entry)
        siemplify.LOGGER.info("Batch full. Sending to Google SecOps.")
        #siemplify.LOGGER.info(json.dumps(log_batch, indent=1))
        c = CollectorUtils.secops.upload(INGESTION_SA_JSON, 
                                            CUSTOMER_ID,
                                            LOG_TYPE,
                                            log_batch
                                            )
        siemplify.LOGGER.info('SecOps API response: ' + c)
        log_batch.clear()
    
if __name__ == "__main__":
    main()