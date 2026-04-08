"""Onfly Hotel URL Generator.

Reads event data, looks up cities in BigQuery, and generates
Onfly hotel booking URLs for corporate travel.
"""

import json
import logging
import os
from dataclasses import dataclass
from urllib.parse import urlencode

from app.services.flight_service import (
    BASE_URL,
    CITY_ALIAS,
    DEFAULT_TRAVELLER,
    Traveller,
    _resolve_city,
    _to_js_date,
)

logger = logging.getLogger(__name__)


@dataclass
class City:
    """City from BigQuery (luna_destination.cities + destinations)."""
    city_id: str
    country_code: str
    state_code: str | None
    name: str
    place_id: str

    def to_url_dict(self) -> dict:
        return {
            "city": {
                "countryCode": self.country_code,
                "name": self.name,
                "stateCode": self.state_code,
            },
            "id": self.city_id,
            "isCity": True,
            "matchSearch": [],
            "name": self.name,
            "placeId": self.place_id,
            "firstCity": True,
        }


def _fetch_cities(bq_client, city_names: list[str]) -> dict[str, City]:
    """Fetch cities from BigQuery for given city names."""
    if not city_names:
        return {}

    gcp_project = os.getenv("GCP_PROJECT_ID", "dw-onfly-dev")
    bq_dataset = os.getenv("BQ_DATASET", "luna_destination")

    conditions = " OR ".join(
        [f"LOWER(d.name) LIKE LOWER('%{c}%')" for c in city_names]
    )

    query = f"""
    SELECT
        c.id            AS city_id,
        c.country_code,
        c.state_code,
        d.name          AS dest_name,
        d.place_id      AS dest_place_id
    FROM `{gcp_project}.{bq_dataset}.cities` c
    JOIN `{gcp_project}.{bq_dataset}.destinations` d
        ON c.destination_id = d.id
    WHERE ({conditions})
    ORDER BY d.name
    """

    rows = list(bq_client.query(query).result())

    cities: dict[str, City] = {}
    for row in rows:
        key = row.dest_name.lower()
        if key not in cities:
            cities[key] = City(
                city_id=row.city_id,
                country_code=row.country_code,
                state_code=row.state_code,
                name=row.dest_name,
                place_id=row.dest_place_id,
            )
    return cities


def build_hotel_url(
    city: City,
    from_date: str,
    to_date: str,
    traveller: Traveller | None = None,
    guests_quantity: int = 1,
) -> str:
    """Build Onfly hotel booking URL."""
    rooms = [{"guestsQuantity": guests_quantity, "travelerIds": []}]

    params = {
        "type": "hotels",
        "city": json.dumps(city.to_url_dict()),
        "fromDate": _to_js_date(from_date),
        "toDate": _to_js_date(to_date),
        "rooms": json.dumps(rooms),
    }
    if traveller:
        params["selectedTravellers"] = json.dumps([traveller.to_url_dict()])

    return f"{BASE_URL}?{urlencode(params)}"


def generate_hotel_url_for_event(
    event_city: str | None,
    event_start_date: str,
    event_end_date: str,
) -> dict:
    """
    Generate a hotel booking URL for a specific event.

    Returns dict with 'url' (str or None) and 'error' (str or None).
    """
    try:
        from google.cloud import bigquery
        bq = bigquery.Client(project=os.getenv("GCP_PROJECT_ID", "dw-onfly-dev"))
    except Exception as exc:
        logger.warning("BigQuery not available: %s", exc)
        return {"url": None, "error": "Serviço de hotéis indisponível"}

    dest_city = _resolve_city(event_city)

    if not dest_city:
        return {"url": None, "error": f"Cidade não mapeada: {event_city}"}

    cities = _fetch_cities(bq, [dest_city])
    city_obj = cities.get(dest_city)

    if not city_obj:
        return {"url": None, "error": f"Cidade não encontrada: {event_city}"}

    try:
        url = build_hotel_url(
            city=city_obj,
            from_date=event_start_date,
            to_date=event_end_date,
        )
        return {"url": url, "error": None}
    except Exception as exc:
        return {"url": None, "error": str(exc)}
