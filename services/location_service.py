"""Malaysia location lookup used by customer registration.

Data source: heiswayi/malaysia-postcodes (CC BY 4.0), version 2025.1.
The source groups postcodes by state and city, which keeps registration
location values consistent without accepting unverified free-text entries.
"""

import json
from functools import lru_cache
from urllib.error import URLError
from urllib.request import urlopen


MALAYSIA_POSTCODES_URL = (
    "https://raw.githubusercontent.com/heiswayi/malaysia-postcodes/"
    "main/data/json/postcodes.json"
)

_STATE_NAMES = {
    "wp kuala lumpur": "W.P. Kuala Lumpur",
    "wilayah persekutuan kuala lumpur": "W.P. Kuala Lumpur",
    "wp labuan": "W.P. Labuan",
    "wilayah persekutuan labuan": "W.P. Labuan",
    "wp putrajaya": "W.P. Putrajaya",
    "wilayah persekutuan putrajaya": "W.P. Putrajaya",
}


def _canonical_state(name: str) -> str:
    key = " ".join((name or "").lower().replace(".", "").split())
    return _STATE_NAMES.get(key, name)


@lru_cache(maxsize=1)
def malaysia_locations() -> dict[str, dict[str, list[str]]]:
    """Return state -> city -> valid postcode list from the public dataset."""
    try:
        with urlopen(MALAYSIA_POSTCODES_URL, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, ValueError, OSError):
        return {}

    locations: dict[str, dict[str, list[str]]] = {}
    for state in payload.get("states", []):
        state_name = _canonical_state(state.get("name", ""))
        cities = locations.setdefault(state_name, {})
        for city in state.get("cities", []):
            city_name = city.get("name", "").strip()
            postcodes = sorted({str(code) for code in city.get("postcodes", [])})
            if city_name and postcodes:
                cities[city_name] = postcodes
    return locations


def cities_for_state(state: str) -> list[str]:
    return sorted(malaysia_locations().get(state, {}))


def postcodes_for_city(state: str, city: str) -> list[str]:
    return malaysia_locations().get(state, {}).get(city, [])
