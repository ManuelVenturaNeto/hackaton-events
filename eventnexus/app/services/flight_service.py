"""Onfly Flight URL Generator.

Reads event data, looks up airports in BigQuery, and generates
Onfly booking URLs for corporate travel.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

BASE_URL = "https://app.onfly.com/travel/#/travel/booking/search"
BRT = timezone(timedelta(hours=-3))

# City name aliases: event city -> BigQuery city name
CITY_ALIAS: dict[str, str] = {
    "boston": "boston",
    "são paulo": "são paulo",
    "sao paulo": "são paulo",
    "san francisco": "são francisco",
    "gramado": "porto alegre",
    "toronto": "toronto",
    "porto alegre": "porto alegre",
    "las vegas": "las vegas",
    "san jose": "san josé",
    "menlo park": "são francisco",
    "beijing": "pequim",
    "dubai": "dubai",
    "rio de janeiro": "rio de janeiro",
    "ribeirão preto": "ribeirão preto",
    "sertãozinho": "ribeirão preto",
    "lisbon": "lisboa",
    "chicago": "chicago",
    "barcelona": "barcelona",
    "belo horizonte": "belo horizonte",
    "new york": "nova iorque",
    "london": "londres",
    "paris": "paris",
    "tokyo": "tóquio",
    "singapore": "singapura",
    "sydney": "sydney",
    "amsterdam": "amsterdam",
    "montreal": "montreal",
    "vancouver": "vancouver",
    "austin": "austin",
    "orlando": "orlando",
    "miami": "miami",
    "buenos aires": "buenos aires",
    "santiago": "santiago",
    "bogota": "bogotá",
    "mexico city": "cidade do méxico",
    "curitiba": "curitiba",
    "brasília": "brasília",
    "brasilia": "brasília",
    "recife": "recife",
    "salvador": "salvador",
    "fortaleza": "fortaleza",
    "campinas": "campinas",
    "florianópolis": "florianópolis",
    "florianopolis": "florianópolis",
    "manaus": "manaus",
    "belém": "belém",
    "belem": "belém",
    "goiânia": "goiânia",
    "goiania": "goiânia",
    "mountain view": "são francisco",
    "seattle": "seattle",
    "los angeles": "los angeles",
    "denver": "denver",
    "atlanta": "atlanta",
    "dallas": "dallas",
    "houston": "houston",
    "washington": "washington",
}


@dataclass
class Airport:
    airport_id: str
    code: str
    type: str
    display_name: str | None
    country_code: str
    state_code: str | None
    airport_name: str
    airport_place_id: str
    city_name: str
    city_place_id: str

    def to_url_dict(self) -> dict:
        return {
            "city": {
                "countryCode": self.country_code,
                "name": self.city_name,
                "placeId": self.city_place_id,
                "stateCode": self.state_code,
            },
            "code": self.code,
            "displayName": self.display_name,
            "id": self.airport_id,
            "matchSearch": [],
            "name": self.airport_name,
            "placeId": self.airport_place_id,
            "type": self.type,
        }


@dataclass
class Traveller:
    id: str = ""
    user_id: str = ""
    organization_id: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone_idd: str = "+55"
    phone_number: str = ""
    birthday: str = ""
    nationality: str = "Brasileiro"
    gender: str = "Male"
    passport: str = ""
    rg: str = ""
    cpf: str = ""
    created_at: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_url_dict(self) -> dict:
        docs = []
        if self.passport:
            docs.append({"documentType": "PASSPORT", "documentValue": self.passport})
        if self.rg:
            docs.append({"documentType": "RG", "documentValue": self.rg})
        if self.cpf:
            docs.append({"documentType": "CPF", "documentValue": self.cpf})

        return {
            "id": self.id or str(uuid.uuid4()),
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "fullName": self.full_name,
            "email": self.email,
            "phone": {
                "id": str(uuid.uuid4()),
                "idd": self.phone_idd,
                "number": self.phone_number,
            },
            "birthday": self.birthday,
            "nationality": self.nationality,
            "gender": self.gender,
            "documents": docs,
            "createdAt": self.created_at or datetime.now().strftime("%Y-%m-%d"),
            "actorId": None,
        }


# Default demo traveller
DEFAULT_TRAVELLER = Traveller(
    id="901125a4-c367-4079-9248-3dd8d72663bc",
    user_id="521204",
    organization_id="3571",
    first_name="Manuel Ventura",
    last_name="Oliveira Neto",
    email="manuel.ventura+99@onfly.com.br",
    phone_number="31983587160",
    birthday="1999-03-04",
    passport="FS076719",
    rg="MG19717132",
    cpf="02138291693",
    created_at="2025-02-14",
)


def _to_js_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to JS Date string format."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=12, tzinfo=BRT)
    return dt.strftime("%a %b %d %Y %H:%M:%S GMT-0300 (Hora padrão de Brasília)")


def _resolve_city(event_city: str | None) -> str | None:
    """Resolve event city name to BigQuery city name."""
    if not event_city:
        return None
    return CITY_ALIAS.get(event_city.lower())


def _fetch_airports(bq_client, city_names: list[str]) -> dict[str, Airport]:
    """Fetch airports from BigQuery for given city names."""
    if not city_names:
        return {}

    gcp_project = os.getenv("GCP_PROJECT_ID", "dw-onfly-dev")
    bq_dataset = os.getenv("BQ_DATASET", "luna_destination")

    city_conditions = " OR ".join(
        [f"LOWER(d_city.name) LIKE LOWER('%{c}%')" for c in city_names]
    )

    query = f"""
    SELECT
        a.id            AS airport_id,
        a.code          AS code,
        a.type          AS type,
        a.display_name  AS display_name,
        c.country_code  AS country_code,
        c.state_code    AS state_code,
        d_airport.name     AS airport_name,
        d_airport.place_id AS airport_place_id,
        d_city.name        AS city_name,
        d_city.place_id    AS city_place_id
    FROM `{gcp_project}.{bq_dataset}.airports` a
    JOIN `{gcp_project}.{bq_dataset}.cities` c
        ON a.city_id = c.id
    JOIN `{gcp_project}.{bq_dataset}.destinations` d_airport
        ON a.destination_id = d_airport.id
    JOIN `{gcp_project}.{bq_dataset}.destinations` d_city
        ON c.destination_id = d_city.id
    WHERE a.type = 'Airport'
      AND ({city_conditions})
    ORDER BY d_city.name, COALESCE(a.score, 0) DESC
    """

    rows = bq_client.query(query).result()

    best: dict[str, Airport] = {}
    for row in rows:
        key = row.city_name.lower()
        if key not in best:
            best[key] = Airport(
                airport_id=row.airport_id,
                code=row.code,
                type=row.type,
                display_name=row.display_name,
                country_code=row.country_code,
                state_code=row.state_code,
                airport_name=row.airport_name,
                airport_place_id=row.airport_place_id,
                city_name=row.city_name,
                city_place_id=row.city_place_id,
            )
    return best


def build_flight_url(
    origin: Airport,
    destination: Airport,
    outbound_date: str,
    inbound_date: str,
    traveller: Traveller | None = None,
) -> str:
    """Build Onfly booking URL."""
    if traveller is None:
        traveller = DEFAULT_TRAVELLER

    params = {
        "type": "flights",
        "origin": json.dumps(origin.to_url_dict()),
        "destination": json.dumps(destination.to_url_dict()),
        "outboundDate": _to_js_date(outbound_date),
        "inboundDate": _to_js_date(inbound_date),
        "passengers": json.dumps({"label": "1", "value": 1}),
        "selectedTravellers": json.dumps([traveller.to_url_dict()]),
    }

    return f"{BASE_URL}?{urlencode(params)}"


def generate_flight_url_for_event(
    event_city: str | None,
    event_start_date: str,
    event_end_date: str,
    origin_city: str = "belo horizonte",
) -> dict:
    """
    Generate a flight booking URL for a specific event.

    Returns dict with 'url' (str or None) and 'error' (str or None).
    """
    try:
        from google.cloud import bigquery
        bq = bigquery.Client(project=os.getenv("GCP_PROJECT_ID", "dw-onfly-dev"))
    except Exception as exc:
        logger.warning("BigQuery not available: %s", exc)
        return {"url": None, "error": "Serviço de voos indisponível"}

    dest_city = _resolve_city(event_city)
    origin_resolved = _resolve_city(origin_city) or origin_city.lower()

    if not dest_city:
        return {"url": None, "error": f"Cidade não mapeada: {event_city}"}

    cities = list({dest_city, origin_resolved})
    airports = _fetch_airports(bq, cities)

    origin_airport = airports.get(origin_resolved)
    if not origin_airport:
        return {"url": None, "error": f"Aeroporto de origem não encontrado: {origin_city}"}

    dest_airport = airports.get(dest_city)
    if not dest_airport:
        return {"url": None, "error": f"Aeroporto de destino não encontrado: {event_city}"}

    try:
        url = build_flight_url(
            origin=origin_airport,
            destination=dest_airport,
            outbound_date=event_start_date,
            inbound_date=event_end_date,
        )
        return {"url": url, "error": None}
    except Exception as exc:
        return {"url": None, "error": str(exc)}
