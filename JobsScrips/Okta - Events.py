from SiemplifyJob import SiemplifyJob
import google.auth.transport.requests
from google.oauth2 import service_account
import json
import requests
import re
from datetime import datetime, timedelta
import CollectorUtils


INTEGRATION_NAME = "Unofficial SecOps API Collectors"
SCRIPT_NAME = "Okta - Events"

siemplify = SiemplifyJob()
siemplify.script_name = SCRIPT_NAME

# INIT INTEGRATION CONFIGURATION:
API_KEY = siemplify.extract_job_param(param_name="Okta API Key", print_value=True)
OKTA_DOMAIN = siemplify.extract_job_param(param_name="Okta Domain", print_value=True)
TIME_INTERVAL = siemplify.extract_job_param(param_name="Job interval (minutes)", print_value=True)
INGESTION_SA_JSON = siemplify.extract_job_param(param_name="SecOps Ingestion API v2 JSON", print_value=False)
INGESTION_SA_JSON = json.loads(INGESTION_SA_JSON)
CUSTOMER_ID = siemplify.extract_job_param(param_name="SecOps Customer ID", print_value=False)

# Log types: https://cloud.google.com/chronicle/docs/ingestion/parser-list/supported-default-parsers
LOG_TYPE = "OKTA"
log_batch = []

def main():

    try:

        d = datetime.now() - timedelta(hours=0, minutes=int(TIME_INTERVAL))
        d = d.strftime('%Y-%m-%dT%H:%M:00.0Z')
        siemplify.LOGGER.info("Current zulu time: " + d)
        
        url = "https://" + OKTA_DOMAIN + "/api/v1/logs?since=" + d
        while url != False:
            url = get_okta_events(url)

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

def get_okta_events(url):
    headers = {
        "Accept":         "application/json",
        "Content-Type":   "applicaiton/json",
        "Authorization":  "SSWS " + API_KEY
    }

    req = requests.get(url=url,headers=headers)
    siemplify.LOGGER.info("Okta API Response: " + req.text)
    page_urls = dict(req.headers)['link'].split(' ')
    url_self = re.sub(r"<|>|;", "", page_urls[0])
    url_next = re.sub(r"<|>|;", "", page_urls[2])
    siemplify.LOGGER.info(url_self)
    siemplify.LOGGER.info(url_next)
    if url_self == url_next:
        js = json.loads(req.text)
        for i in js:
            batch_logs(i)
        return False
    else:
        js = json.loads(req.text)
        for i in js:
            batch_logs(i)
        return url_next

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