# Unofficial API Collectors for Google SecOps
Unofficial set of "jobs" for Google SecOps that allows you to collect events from 3rd-party APIs that aren't directly supported by SecOps's Feed Managment. These are mean to serve as a reference for collecting data from 3rd-party APIs and batch ingest those events in SecOps.


## Integration Configuration
| Parameter  | Description |
| ------------- | ------------- |
| SecOps Ingestion API v2 JSON | Ingestion API credential. Available from your Google/SecOps partner team or via the interface under `SIEM Settings` -> `Collection Agents` -> `Ingestion Authentication File` |
| Google SecOps Customer ID | Your customer/tenant ID for Google SecOps. Available in interface under `SIEM Settings` -> `Profile` -> `Customer ID` |


## Available Collectors
| Event Source | Description | API Documentation |
| ------------- | ------------- | ------------- |
| ADSBFI Live Aircraft Feed | Collects ADS-B flight data around a geographic point using ADSB.FI free API | [Link](https://github.com/adsbfi/opendata/blob/main/README.md) |
| Okta - Events | Collects Okta events | [Link](https://developer.okta.com/docs/reference/api/system-log/) |
