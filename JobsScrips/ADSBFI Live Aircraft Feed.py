from SiemplifyJob import SiemplifyJob
import json
import requests
from datetime import datetime
import CollectorUtils

INTEGRATION_NAME = "Unofficial SecOps API Collectors"
SCRIPT_NAME = "ADSBFI Live Aircraft Feed"

siemplify = SiemplifyJob()
siemplify.script_name = SCRIPT_NAME
# INIT INTEGRATION CONFIGURATION:
dist = siemplify.extract_job_param(param_name="Distance", print_value=True)
latitude = siemplify.extract_job_param(param_name="Latitude", print_value=True)
longitude = siemplify.extract_job_param(param_name="Longitude", print_value=True)
INGESTION_SA_JSON = siemplify.extract_job_param(param_name="SecOps Ingestion API v2 JSON", print_value=False)
INGESTION_SA_JSON = json.loads(INGESTION_SA_JSON)
CUSTOMER_ID = siemplify.extract_job_param(param_name="SecOps Customer ID", print_value=False)

# Log types: https://cloud.google.com/chronicle/docs/ingestion/parser-list/supported-default-parsers
LOG_TYPE = "UDM"
log_batch = []

def main():

    try:
        headers = {
            "Accept":         "application/json",
            "Content-Type":   "applicaiton/json"
        }
        
        # https://github.com/adsbfi/opendata/blob/main/README.md
        url = "https://opendata.adsb.fi/api/v2/lat/" + latitude 
        url = url + "/lon/" + longitude + "/dist/" + dist
        req = requests.get(url=url,headers=headers)
        siemplify.LOGGER.info("ads.fi response: " + req.text)
        js = json.loads(req.text)
        for i in js["aircraft"]:
            if 'flight' in i:
                # Strip out the whitespace from the flight number
                flight = i["flight"]
                flight = flight.replace(' ', '')
                i["flight"] = flight

                # Create an app name to send along to our SIEM
                i["app_name"] = "ADSB.FI Aircraft Tracking"

                # Let's also send a timestamp
                d = datetime.now()
                d = d.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                i["date_time"] = d
                batch_logs(i)
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

def batch_logs(log_line):
    batch_size = len(json.dumps(log_batch).encode())
    siemplify.LOGGER.info('Batch size: ' + str(batch_size))
    # Batch size is limited to 1 MB: https://cloud.google.com/chronicle/docs/reference/ingestion-api#unstructuredlogentries
    if batch_size < 800000:
        entry = { "log_text": json.dumps(log_line) }
        log_batch.append(entry)
    else:
        entry = { "log_text": json.dumps(log_line) }
        log_batch.append(entry)
        siemplify.LOGGER.info("Batch full. Sending to Google SecOps.")
        c = CollectorUtils.secops.upload(INGESTION_SA_JSON, 
                                            CUSTOMER_ID,
                                            LOG_TYPE,
                                            log_batch
                                            )
        siemplify.LOGGER.info('SecOps API response: ' + c)
        log_batch.clear()

if __name__ == "__main__":
    main()