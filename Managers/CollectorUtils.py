import google.auth.transport.requests
from google.oauth2 import service_account
import requests
import json

class secops():
    def __init__(self):#self
        pass
        
    def upload(INGESTION_SA_JSON, CUSTOMER_ID, LOG_TYPE, LOG_BATCH):
        credentials = service_account.Credentials.from_service_account_info(
            INGESTION_SA_JSON, 
            scopes=['https://www.googleapis.com/auth/malachite-ingestion']
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        hd = {
            "Authorization": "Bearer " + credentials.token,
            "Content-Type": "application/json"
        }
        
        raw_event = {
            "customer_id": CUSTOMER_ID,
            "log_type": LOG_TYPE,
            "entries": LOG_BATCH
        }
    
        req = requests.post('https://malachiteingestion-pa.googleapis.com/v2/unstructuredlogentries:batchCreate',
            headers=hd, 
            json=raw_event
            )
        return(req.text)

    def upload_via_dataplane(INGESTION_SA_JSON, CUSTOMER_ID, FORWARDER_ID, LOG_TYPE, LOG_BATCH):
        credentials = service_account.Credentials.from_service_account_info(
            INGESTION_SA_JSON, 
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        hd = {
            "Authorization": "Bearer " + credentials.token,
            "Content-Type": "application/json"
        }

        # Extract the required project ID from the service account JSON
        project_id = INGESTION_SA_JSON['project_id']
        
        payload = {
                    'inline_source' : {
                        'logs' : LOG_BATCH,
                        "forwarder" : f"projects/{project_id}/locations/us/instances/{CUSTOMER_ID}/forwarders/{FORWARDER_ID}"
                    }
        }
        endpoint = f"https://us-chronicle.googleapis.com/v1alpha/projects/{project_id}/locations/us/instances/{CUSTOMER_ID}/logTypes/{LOG_TYPE}/logs:import"
    
        req = requests.post(url=endpoint,
            headers=hd, 
            json=payload
            )
        return(req.text)