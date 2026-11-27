![resources/logo.svg](resources/logo.svg)
# Transit Departures Finland

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

[![Community Forum][forum-shield]][forum]

Home Assistant custom integration for upcoming departures from the FinTraffic GraphQL API.

## Features

- Uses [FinTraffic open APIs](https://www.digitraffic.fi/en/) for public transit per-stop departure times
- Shared config entry for departure settings, plus one stop subentry per configured stop
- One stop-specific sensor per configured stop
- Stop setup by REST-based name lookup or manual GTFS id entry
- Configurable API polling interval with a default of 15 minutes
- Sensor values and attributes recalculated every minute from the latest retrieved data
- Timestamp sensor state for the next valid departure after the cutoff window
- Attributes for the primary departure, following departures, and active alerts

## Installation

### Marketplace

Requires Home Assistant 2026.11.0 or later.

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=mickut&repository=ha-transit-departures&category=integration)

1. Open the link above, or go to **Settings > Marketplace** and select **Add from link**.
2. If prompted, connect GitHub and add `https://github.com/mickut/ha-transit-departures` as an integration.
3. Open Transit Departures Finland and select **Install**.
4. Follow the setup prompt, or go to **Settings > Devices & services > Add integration** and search for Transit Departures Finland,
   or use the badge below.

A first install normally loads without a restart. Follow any restart prompt shown by Home Assistant;
updates to a loaded integration require a restart.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=transit_departures_finland)

### Upgrading from 0.4.2 or earlier

Version 0.4.3 changes the integration domain from `transit_departures` to
`transit_departures_finland` to avoid a conflict with another integration.
Settings and stop subentries are not migrated. Note your settings and stop IDs
before removing the old integration; entity IDs may change and automations or
dashboards may need updating.

1. In **Settings > Devices & services**, remove the existing Transit Departures Finland integration.
2. If installed through Marketplace, uninstall its repository there. If installed
   manually, remove the old `custom_components/transit_departures` folder.
   Do this before installing the other integration that uses that domain.
3. Restart Home Assistant, install the new version using the instructions above,
   and add the integration and its stops again.

### Manual installation

1. Download a release or this repository.
2. Copy the `custom_components/transit_departures_finland` folder into your Home Assistant `config/custom_components` directory.
3. Restart Home Assistant.
4. Go to Settings > Devices & services > Add integration and search for Transit Departures Finland.

## Configuration

The main config flow asks for (all numeric settings can be changed later
with **Reconfigure** on the integration entry):

- `number_of_departures`: how many departures to retain after sorting and filtering.
  Each stop can override this: open the integration page, then use **Reconfigure**
  on the stop's row. Unset stops follow the shared value.
- `cutoff_minutes`: exclude departures that are in the past or within this many minutes from now
- `update_interval_minutes`: API polling interval for refreshing departures, default `15`
- `prefix` (optional): text prepended to each sensor name, default empty
- `suffix` (optional): text appended to each sensor name, default `Next Departure`

Both `prefix` and `suffix` can be changed or cleared later using **Configure** on the
integration entry. If both are left empty, each sensor is named after its stop.

After the main entry is created, Home Assistant opens a stop subentry flow for the first stop. Additional stops can be added later from the integration page.

Each stop can be added in one of two ways:

- Search by stop name using the DigiTransit geocoding endpoint and select one matching stop
- Enter the stop GTFS id manually, for example `MATKA:12345`

## Sensor behavior

Each sensor uses the next departure datetime as its state. Route names and related metadata are exposed in attributes because a Home Assistant sensor state can only hold one value. The integration recalculates sensor state and attributes once a minute from cached API data, while the external API call itself follows the configured interval.

Main attributes:

- `primary_departure`
- `next_departures`
- `alerts`
- `stop_id`
- `stop_name`

## Local development (VS Code)

### Minimum required venv

The minimum supported local development environment is:

- Python `3.14+` (this project currently targets `3.14`)
- A virtual environment in `.venv`
- Test extras installed from this project (`homeassistant`, `pytest`, `pytest-asyncio`, `pytest-socket`, `pytest-cov`)

Windows setup:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[test]
```

Quick verification:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

Recommended workspace settings for running tests from the project virtual environment and enabling coverage by default in the VS Code test runner:

```json
{
 "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
 "python.testing.pytestEnabled": true,
 "python.testing.pytestArgs": [
  "tests",
  "--cov=custom_components/transit_departures_finland",
  "--cov-report=term-missing",
  "--cov-report=xml"
 ]
}
```

Notes:
- If needed, you can run the same command in a terminal with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests --cov=custom_components/transit_departures_finland --cov-report=term-missing --cov-report=xml
```

***

[commits-shield]: https://img.shields.io/github/commit-activity/y/mickut/ha-transit-departures.svg?style=for-the-badge
[commits]: https://github.com/mickut/ha-transit-departures/commits/main
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/mickut/ha-transit-departures.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Antti%20Kuntsi%20%40mickut-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/mickut/ha-transit-departures.svg?style=for-the-badge
[releases]: https://github.com/mickut/ha-transit-departures/releases
