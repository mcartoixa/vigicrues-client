# Recorded Vigicrues responses

Real responses from [Vigicrues](https://www.vigicrues.gouv.fr), recorded so that tests can check the
parsing without calling the service. Files are stored exactly as received, quirks included (git
treats them as binary to keep their line endings, CRLF in most of them: see `.gitattributes`). The
service redirected (HTTP 302) the requests to `TerEntVigiCru.json`, `TronEntVigiCru.json` and
`StaEntVigiCru.json` (to `/services/<name>.json`), `observations.json` and `station.json` (to
`/services/<name>.json/index.php`), `/services/1/InfoVigiCru.geojson` (to
`/services/InfoVigiCru.geojson`); the status and content type are those of the final response.
`station_unknown.html` is the generic "Site en maintenance" page: `/bulletin_local/99` and
`/bulletin_local/0` (unknown territories) got the same bytes on 2026-11-22 08:49 UTC.

Exceptions:

- `observations_E540031001_Q_trimmed.json` keeps only the first 2 and the last 3 of the 20,806
  observations received (1.27 MB), byte for byte, the rest of the body being unchanged.
- `InfoVigiCru_trimmed.geojson` keeps only 7 of the 337 river sections received (2.2 MB): the 5
  not in green vigilance (`RS18`, `RS31`, `RS41`, `NO14` yellow, `AP16` orange), `MP18` and the
  last one, `DO10` (both green). The service sends one river section per line: the lines kept are
  byte for byte, the first two and the last one (the production time) included.
- `StaEntVigiCru_all_trimmed.json` keeps only 4 of the 2,376 stations received (1.7 MB): the first
  two (Guyane), `E540031001` (Brimeux) and the last one. Each station is a block of lines kept
  byte for byte, the rest of the body (`"count": 2376` included) being unchanged.

Vigicrues content is published under the
[Etalab Open Licence 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/).

| File | Request | Status | Content type | Recorded on |
|---|---|---|---|---|
| `bulletin_local_18.html` | `/bulletin_local/18` | 200 | `text/html; charset=UTF-8` | 2026-11-22 08:49 UTC |
| `bulletin_local_25.html` | `/bulletin_local/25` | 200 | `text/html; charset=UTF-8` | 2026-11-22 08:49 UTC |
| `bulletin_local_29.html` | `/bulletin_local/29` | 200 | `text/html; charset=UTF-8` | 2026-11-22 08:49 UTC |
| `InfoVigiCru_trimmed.geojson` | `/services/1/InfoVigiCru.geojson` | 200 | `application/json; charset=utf-8` | 2026-11-22 08:16 UTC |
| `observations_E540031001_Q_trimmed.json` | `/services/observations.json?CdStationHydro=E540031001&GrdSerie=Q&FormatDate=iso` | 200 | `application/json` | 2026-11-21 19:06 UTC |
| `observations_O262002001_Q.json` | `/services/observations.json?CdStationHydro=O262002001&GrdSerie=Q&FormatDate=iso` | 200 | `application/json` | 2026-11-21 19:06 UTC |
| `observations_O262002001.json` | `/services/observations.json?CdStationHydro=O262002001&FormatDate=iso` | 200 | `application/json` | 2026-11-21 18:55 UTC |
| `observations_unknown.json` | `/services/observations.json?CdStationHydro=X000000000` | 200 | `application/json` | 2026-11-21 18:27 UTC |
| `page_not_found.html` | `/services/1/InfoVigiCru.json` | 404 | `text/html; charset=UTF-8` | 2026-11-21 18:27 UTC |
| `prevision_E540031001.json` | `/services/v1.1/prevision.json?CdEntVigiCru=E540031001&TypEntVigiCru=7&GrdSimul=H&FormatDate=iso` | 200 | `application/json;charset=UTF-8` | 2026-11-23 19:10 UTC |
| `prevision_E540031001_Q.json` | `/services/v1.1/prevision.json?CdEntVigiCru=E540031001&TypEntVigiCru=7&GrdSimul=Q&FormatDate=iso` | 200 | `application/json;charset=UTF-8` | 2026-11-23 19:10 UTC |
| `prevision_invalid_quantity.json` | `/services/v1.1/prevision.json?CdEntVigiCru=E540031001&TypEntVigiCru=7&GrdSimul=X&FormatDate=iso` | 200 | `application/json;charset=UTF-8` | 2026-11-23 19:10 UTC |
| `prevision_no_forecast.json` | `/services/v1.1/prevision.json?CdEntVigiCru=O262002001&TypEntVigiCru=7` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:28 UTC |
| `prevision_not_forecast_station.json` | `/services/v1.1/prevision.json?CdEntVigiCru=E541000401&TypEntVigiCru=7&GrdSimul=H&FormatDate=iso` | 200 | `application/json;charset=UTF-8` | 2026-11-23 19:10 UTC |
| `prevision_unknown.json` | `/services/v1.1/prevision.json?CdEntVigiCru=X000000000&TypEntVigiCru=7&GrdSimul=H&FormatDate=iso` | 200 | `application/json;charset=UTF-8` | 2026-11-23 19:10 UTC |
| `StaEntVigiCru_all_trimmed.json` | `/services/v1.1/StaEntVigiCru.json` | 200 | `application/json;charset=UTF-8` | 2026-11-23 19:22 UTC |
| `StaEntVigiCru_E540031001.json` | `/services/v1.1/StaEntVigiCru.json?CdEntVigiCru=E540031001&TypEntVigiCru=7` | 200 | `application/json;charset=UTF-8` | 2026-11-21 19:11 UTC |
| `StaEntVigiCru_unknown.json` | `/services/v1.1/StaEntVigiCru.json?CdEntVigiCru=X000000000&TypEntVigiCru=7` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:27 UTC |
| `station_E540031001.json` | `/services/station.json?CdStationHydro=E540031001` | 200 | `application/json` | 2026-11-21 19:10 UTC |
| `station_E541000401.json` | `/services/station.json?CdStationHydro=E541000401` | 200 | `application/json` | 2026-11-21 19:11 UTC |
| `station_invalid.json` | `/services/station.json?CdStationHydro=E54003100` | 200 | `application/json` | 2026-11-22 07:33 UTC |
| `station_unknown.html` | `/services/station.json?CdStationHydro=X000000000` | 500 | `text/html` | 2026-11-21 18:27 UTC |
| `TerEntVigiCru_0.json` | `/services/v1.1/TerEntVigiCru.json?CdEntVigiCru=0&TypEntVigiCru=5` | 200 | `application/json;charset=UTF-8` | 2026-11-22 07:03 UTC |
| `TerEntVigiCru_all.json` | `/services/v1.1/TerEntVigiCru.json` | 200 | `application/json;charset=UTF-8` | 2026-11-23 19:22 UTC |
| `TerEntVigiCru_25.json` | `/services/v1.1/TerEntVigiCru.json?CdEntVigiCru=25&TypEntVigiCru=5` | 200 | `application/json;charset=UTF-8` | 2026-11-22 07:03 UTC |
| `TerEntVigiCru_unknown.json` | `/services/v1.1/TerEntVigiCru.json?CdEntVigiCru=99&TypEntVigiCru=5` | 200 | `application/json;charset=UTF-8` | 2026-11-22 07:04 UTC |
| `TronEntVigiCru_all.json` | `/services/v1.1/TronEntVigiCru.json` | 200 | `application/json;charset=UTF-8` | 2026-11-23 19:22 UTC |
| `TronEntVigiCru_AP16.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=AP16&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:31 UTC |
| `TronEntVigiCru_invalid.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=ap16&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-22 07:07 UTC |
| `TronEntVigiCru_MP1.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=MP1&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-22 07:07 UTC |
| `TronEntVigiCru_MP18.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=MP18&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-22 09:14 UTC |
| `TronEntVigiCru_missing_type.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=AP16` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:28 UTC |
| `TronEntVigiCru_P16.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=P16&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-22 07:04 UTC |
| `TronEntVigiCru_RS17.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=RS17&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-22 09:14 UTC |
| `TronEntVigiCru_territory_25.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=25&TypEntVigiCru=5` | 200 | `application/json;charset=UTF-8` | 2026-11-22 07:03 UTC |
| `TronEntVigiCru_unknown.json` | `/services/v1.1/TronEntVigiCru.json?CdEntVigiCru=MP6&TypEntVigiCru=8` | 200 | `application/json;charset=UTF-8` | 2026-11-21 18:27 UTC |
