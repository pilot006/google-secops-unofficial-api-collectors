# Unofficial API Collectors for Google SecOps
Unofficial set of "jobs" for Google SecOps that allows you to collect events from 3rd-party APIs that aren't directly supported by SecOps's Feed Managment. These are mean to serve as a reference for collecting data from 3rd-party APIs and batch ingest those events in SecOps.


## Common Configuration - [Chronicle API](https://cloud.google.com/chronicle/docs/reference/ingestion-api) (for all jobs/connectors using Chronicle API)
| Parameter  | Description |
| ------------- | ------------- |
| SecOps Ingestion API v2 JSON | Ingestion API credential. Available from your Google/SecOps partner team or via the interface under `SIEM Settings` -> `Collection Agents` -> `Ingestion Authentication File` |
| Google SecOps Customer ID | Your customer/tenant ID for Google SecOps. Available in interface under `SIEM Settings` -> `Profile` -> `Customer ID` |


## Common Configuration - [Data Plane API](https://cloud.google.com/chronicle/docs/reference/rest/v1alpha/projects.locations.instances.logTypes.logs/import) (for all jobs/connectors using Data Plane API)
| Parameter  | Description |
| ------------- | ------------- |
| Service Account JSON | Service account JSON for SA created in your SecOps GCP project with the following permissions: `chronicle.entities.import`,`chronicle.events.import`,`chronicle.logs.import ` |
| SecOps Customer ID | Your customer/tenant ID for Google SecOps. Available in interface under `SIEM Settings` -> `Profile` -> `Customer ID` |
| SecOps Forwarder Config ID | Config ID for forwarder used for ingestion: https://cloud.google.com/chronicle/docs/install/forwarder-management-configurations#add-forwarders |


## Available Collectors
| Event Source | Description | API Documentation |
| ------------- | ------------- | ------------- |
| ADSBFI Live Aircraft Feed | Collects ADS-B flight data around a geographic point using ADSB.FI free API (supports Chronicle & Data Plane API) | [Link](https://github.com/adsbfi/opendata/blob/main/README.md) |
| Okta - Events | Collects Okta events | [Link](https://developer.okta.com/docs/reference/api/system-log/) |
| 1Password - Audit Events | Collects audit events from 1Password | [Link](https://developer.1password.com/docs/events-api/reference/#post-apiv1auditevents) |
| Google SecOps/Chronicle SOAR | Collects the SOAR audit logs | [Link](https://cloud.google.com/chronicle/docs/soar/reference/working-with-chronicle-soar-apis) |
| Google SecOps/Chronicle SIEM Parser Errors | Collects parser errors for specified log types | [Link](https://cloud.google.com/chronicle/docs/administration/cli-user-guide#parser_management_user_workflows) |
