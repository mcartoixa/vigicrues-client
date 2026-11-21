# Recorded Vigicrues responses

Real responses from [Vigicrues](https://www.vigicrues.gouv.fr), recorded so that tests can check the
parsing without calling the service. Files are stored exactly as received, quirks included (git
treats them as binary to keep their CRLF line endings: see `.gitattributes`). The service
redirected (HTTP 302) the requests to `TronEntVigiCru.json` and `StaEntVigiCru.json` (to
`/services/<name>.json`),
`observations.json` and `station.json` (to `/services/<name>.json/index.php`); the status and
content type are those of the final response.

Exception: `observations_E540031001_Q_trimmed.json` keeps only the first 2 and the last 3 of the
20,806 observations received (1.27 MB), byte for byte, the rest of the body being unchanged.

Vigicrues content is published under the
[Etalab Open Licence 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/).

| File | Request | Status | Content type | Recorded on |
|---|---|---|---|---|
| `observations_E540031001_Q_trimmed.json` | `/services/observations.json?CdStationHydro=E540031001&GrdSerie=Q&FormatDate=iso` | 200 | `application/json` | 2026-11-21 19:06 UTC |
| `observations_O262002001_Q.json` | `/services/observations.json?CdStationHydro=O262002001&GrdSerie=Q&FormatDate=iso` | 200 | `application/json` | 2026-11-21 19:06 UTC |
| `observations_O262002001.json` | `/services/observations.json?CdStationHydro=O262002001&FormatDate=iso` | 200 | `application/json` | 2026-11-21 18:55 UTC |
| `observations_unknown.json` | `/services/observations.json?CdStationHydro=X000000000` | 200 | `application/json` | 2026-11-21 18:27 UTC |
| `page_not_found.html` | `/services/1/InfoVigiCru.json` | 404 | `text/html; charset=UTF-8` | 2026-11-21 18:27 UTC |
| `prevision_no_forecast.json` | `/services/v1.1/prevision.json?CdEntVigiCru=O262002001&TypEntVigiCru=7` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:28 UTC |
| `StaEntVigiCru_E540031001.json` | `/services/v1.1/StaEntVigiCru.json?CdEntVigiCru=E540031001&TypEntVigiCru=7` | 200 | `application/json;charset=UTF-8` | 2026-11-21 19:11 UTC |
| `StaEntVigiCru_unknown.json` | `/services/v1.1/StaEntVigiCru.json?CdEntVigiCru=X000000000&TypEntVigiCru=7` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:27 UTC |
| `station_E540031001.json` | `/services/station.json?CdStationHydro=E540031001` | 200 | `application/json` | 2026-11-21 19:10 UTC |
| `station_E541000401.json` | `/services/station.json?CdStationHydro=E541000401` | 200 | `application/json` | 2026-11-21 19:11 UTC |
| `station_unknown.html` | `/services/station.json?CdStationHydro=X000000000` | 500 | `text/html` | 2026-11-21 18:27 UTC |
| `TronEntVigiCru_AP16.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=AP16&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:31 UTC |
| `TronEntVigiCru_missing_type.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=AP16` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:28 UTC |
| `TronEntVigiCru_unknown.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=MP6&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:27 UTC |
