from SiemplifyJob import SiemplifyJob
import google.auth.transport.requests
from google.oauth2 import service_account
import json
import requests
import base64
from datetime import datetime, timedelta, timezone
import CollectorUtils

INTEGRATION_NAME = "Unofficial SecOps API Collectors"
SCRIPT_NAME = "DataPlane_SecOps SIEM Parser Errors"

siemplify = SiemplifyJob()
siemplify.script_name = SCRIPT_NAME
# INIT INTEGRATION CONFIGURATION:
LOG_TYPES = siemplify.extract_job_param(param_name="SecOps Log Types", print_value=True)
JOB_INTERVAL = siemplify.extract_job_param(param_name="Job Interval (minutes)", print_value=True)
INGESTION_SA_JSON = siemplify.extract_job_param(param_name="Service Account JSON", print_value=False)
INGESTION_SA_JSON = json.loads(INGESTION_SA_JSON)
BK_API_JSON = siemplify.extract_job_param(param_name="Backstory API JSON", print_value=False)
BK_API_JSON = json.loads(BK_API_JSON)
CUSTOMER_ID = siemplify.extract_job_param(param_name="SecOps Customer ID", print_value=False)
FORWARDER_ID = siemplify.extract_job_param(param_name="SecOps Forwarder Config ID", print_value=True)

# Log types: https://cloud.google.com/chronicle/docs/ingestion/parser-list/supported-default-parsers
LOG_TYPE = "CHRONICLE_FEED"
log_batch = []

def main():

    # Generate required dates for use in APInow_utc = datetime.utcnow()
    now_utc = datetime.utcnow()
    end_time = now_utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    start_time = now_utc - timedelta(minutes=int(JOB_INTERVAL))
    start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    try:
        
        log_types_arr = LOG_TYPES.split(",")
        for log in log_types_arr:
            siemplify.LOGGER.info(f'Checking log type {log} for errors')
            endpoint = f"https://backstory.googleapis.com/v1/tools/cbnParsers:listCbnParserErrors?log_type={log}&start_time={start_time}&end_time={end_time}"
            siemplify.LOGGER.info(f"Using API endpoint: {endpoint}")
            err = get_parser_errors(endpoint)
            if 'errors' in err:
                for i in err['errors']:
                    c_index = 0
                    for c in i['logs']:
                        c = base64.b64decode(c).decode('utf-8')
                        i['logs'][c_index] = c
                        c_index = c_index + 1
                    batch_logs(i)
            else:
                siemplify.LOGGER.info(f"No errors found for {log}")
        
        if log_batch != []:
            siemplify.LOGGER.info('Sending non-full batch at end.')
            c = CollectorUtils.secops.upload_via_dataplane(INGESTION_SA_JSON, 
                                            CUSTOMER_ID,
                                            FORWARDER_ID,
                                            LOG_TYPE,
                                            log_batch
                                            )
            siemplify.LOGGER.info('SecOps API response: ' + c)

    except Exception as e:
        siemplify.LOGGER.error("General error performing Job {}".format(SCRIPT_NAME))
        siemplify.LOGGER.exception(e)
        raise

    siemplify.end_script()
    

def get_parser_errors(api_endpoint):
    credentials = service_account.Credentials.from_service_account_info(
        BK_API_JSON, scopes=['https://www.googleapis.com/auth/chronicle-backstory']
        )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    hd = {
        "Authorization": "Bearer " + credentials.token,
        "Content-Type": "application/json"
    }
    req = requests.get(api_endpoint, headers=hd)
    return(req.json())

def batch_logs(log_line):
    batch_size = len(json.dumps(log_batch).encode())
    siemplify.LOGGER.info('Batch size: ' + str(batch_size))
    # Batch size is limited to 1 MB: https://cloud.google.com/chronicle/docs/reference/ingestion-api#unstructuredlogentries
    if batch_size < 800000:
        # Convert JSON object to string
        json_str = json.dumps(log_line)
        # Encode the JSON string to bytes
        json_bytes = json_str.encode('utf-8')
        # Encode the bytes to base64
        base64_bytes = base64.b64encode(json_bytes)
        # Convert base64 bytes to string
        base64_str = base64_bytes.decode('utf-8')
        entry = { "data": base64_str }
        log_batch.append(entry)
    else:
        # Convert JSON object to string
        json_str = json.dumps(log_line)
        # Encode the JSON string to bytes
        json_bytes = json_str.encode('utf-8')
        # Encode the bytes to base64
        base64_bytes = base64.b64encode(json_bytes)
        # Convert base64 bytes to string
        base64_str = base64_bytes.decode('utf-8')
        entry = { "data": base64_str }
        log_batch.append(entry)
        siemplify.LOGGER.info("Batch full. Sending to Google SecOps.")
        c = CollectorUtils.secops.upload_via_dataplane(INGESTION_SA_JSON, 
                                            CUSTOMER_ID,
                                            FORWARDER_ID,
                                            LOG_TYPE,
                                            log_batch
                                            )
        siemplify.LOGGER.info('SecOps API response: ' + c)
        log_batch.clear()

if __name__ == "__main__":
    main()