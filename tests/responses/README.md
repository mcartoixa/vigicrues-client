# Recorded Vigicrues responses

Real responses from [Vigicrues](https://www.vigicrues.gouv.fr), recorded so that tests can check the
parsing without calling the service. Files are stored exactly as received, quirks included (git
treats them as binary to keep their CRLF line endings: see `.gitattributes`). The service
redirected (HTTP 302) the requests to `TronEntVigiCru.json` (to `/services/TronEntVigiCru.json`),
`observations.json` and `station.json` (to `/services/<name>.json/index.php`); the status and
content type are those of the final response.

Vigicrues content is published under the
[Etalab Open Licence 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/).

| File | Request | Status | Content type | Recorded on |
|---|---|---|---|---|
| `observations_unknown.json` | `/services/observations.json?CdStationHydro=X000000000` | 200 | `application/json` | 2026-11-21 18:27 UTC |
| `page_not_found.html` | `/services/1/InfoVigiCru.json` | 404 | `text/html; charset=UTF-8` | 2026-11-21 18:27 UTC |
| `prevision_no_forecast.json` | `/services/v1.1/prevision.json?CdEntVigiCru=O262002001&TypEntVigiCru=7` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:28 UTC |
| `station_unknown.html` | `/services/station.json?CdStationHydro=X000000000` | 500 | `text/html` | 2026-11-21 18:27 UTC |
| `TronEntVigiCru_AP16.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=AP16&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:31 UTC |
| `TronEntVigiCru_missing_type.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=AP16` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:28 UTC |
| `TronEntVigiCru_unknown.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=MP6&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:27 UTC |
