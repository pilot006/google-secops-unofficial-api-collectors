import google.auth.transport.requests
from google.oauth2 import service_account
import requests

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