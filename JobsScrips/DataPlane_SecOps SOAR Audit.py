from SiemplifyJob import SiemplifyJob
import json
import requests
from datetime import datetime,timedelta
import base64
from io import StringIO
import csv
import CollectorUtils

INTEGRATION_NAME = "Unofficial SecOps API Collectors"
SCRIPT_NAME = "DataPlane_SecOps SOAR Audit"

siemplify = SiemplifyJob()
siemplify.script_name = SCRIPT_NAME

# INIT INTEGRATION CONFIGURATION:
SOAR_HOSTNAME = siemplify.extract_job_param(param_name="SOAR Hostname", print_value=True)
JOB_INTERVAL = siemplify.extract_job_param(param_name="Job Interval", print_value=True)
SOAR_API_KEY = siemplify.extract_job_param(param_name="SOAR API Key", print_value=False)
INGESTION_SA_JSON = siemplify.extract_job_param(param_name="Service Account JSON", print_value=False)
INGESTION_SA_JSON = json.loads(INGESTION_SA_JSON)
CUSTOMER_ID = siemplify.extract_job_param(param_name="SecOps Customer ID", print_value=False)
FORWARDER_ID = siemplify.extract_job_param(param_name="SecOps Forwarder Config ID", print_value=True)

# Log types: https://cloud.google.com/chronicle/docs/ingestion/parser-list/supported-default-parsers
LOG_TYPE = "CHRONICLE_SOAR_AUDIT"
log_batch = []

def main():

    try:

        auth_header = {
            'content-type': 'application/json',
            'Appkey' : SOAR_API_KEY
        }
        j = {
            "auditType":1,
            "usersNames":[]
        }
        url = "https://" + SOAR_HOSTNAME + "/api/external/v1/settings/ExportAuditLastWeekAsCsvV2"
        req = requests.post(url=url,headers=auth_header, json=j)
        d = datetime.now() - timedelta(hours=0, minutes=int(JOB_INTERVAL))
        d = d.replace(second=0, microsecond=0)
        siemplify.LOGGER.info("Using this date for comparison: " + str(d))
        if "blob" in req.text:
            js = json.loads(req.text)
            blob = js['blob']
            logs = csv_to_json(blob)
            for s in logs:
                # Let's parse the timestamp to do a time comparison
                date = datetime.strptime(s['Date'], "%m/%d/%Y %H:%M:%S")
                if date > d:
                    siemplify.LOGGER.info('date (' + str(date) + ') > d (' + str(d) + ')')
                    batch_logs(s)
        # If we still have logs in the batch, send them now that we're at the end
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

def csv_to_json(blob):
    # Decode the base64 string
    decoded_data = base64.b64decode(blob).decode('utf-8')
    csv_file = StringIO(decoded_data)
    csv_reader = csv.DictReader(csv_file)
    data = list(csv_reader)
    return data

def batch_logs(log_line):
    batch_size = len(json.dumps(log_batch).encode())
    siemplify.LOGGER.info('Batch size: ' + str(batch_size))
    # Batch size is limited to 1 MB: https://cloud.google.com/chronicle/docs/reference/ingestion-api#unstructuredlogentries
    if batch_size < 800000:
        json_str = json.dumps(log_line)
        json_bytes = json_str.encode('utf-8')
        base64_bytes = base64.b64encode(json_bytes)
        base64_str = base64_bytes.decode('utf-8')
        entry = { "data": base64_str }
        log_batch.append(entry)
    else:
        json_str = json.dumps(log_line)
        json_bytes = json_str.encode('utf-8')
        base64_bytes = base64.b64encode(json_bytes)
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