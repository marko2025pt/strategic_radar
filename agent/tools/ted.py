# Version 1.1 — Final demo delivery to Ironhack 2026-03-06
"""
agent/tools/ted.py

TED EU Open Data API tool for the Strategic Radar agent.
"""

import requests
from datetime import datetime, timedelta
import json
from agent.tools.utils import mcp
from core.logging_config import get_logger

logger = get_logger(__name__)

TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"


# ---------------------------------------------------------------------------
# CPV codes per sector
# ---------------------------------------------------------------------------

SECTOR_CPV_MAP = {
    "QSR and Food Service": [
        "42968100",   # self-service kiosks
        "30213000",   # tablet/touch computers
        "48000000",   # software (ordering systems)
    ],
    "Smart Cities": [
        "32321200",   # video-display equipment
        "48813200",   # electronic notice boards
        "34970000",   # traffic monitoring
        "48000000",   # software
    ],
    "Airport and Transport": [
        "48813200",   # passenger information systems
        "42968100",   # self-service kiosks
        "34980000",   # transport tickets/passes
        "63700000",   # transport support services
    ],
    "Retail": [
        "30213000",   # touch computers
        "42968100",   # self-service kiosks
        "32321200",   # display equipment
    ],
    "Public Services": [
        "42968100",   # self-service kiosks
        "48813200",   # information display systems
        "72000000",   # IT services
        "30213000",   # touch computers
    ],
}


# ---------------------------------------------------------------------------
# Keyword search
# ---------------------------------------------------------------------------

SECTOR_KEYWORDS = {
    "QSR and Food Service":   ["self-service kiosk", "ordering kiosk", "food ordering terminal"],
    "Smart Cities":           ["digital signage", "smart kiosk", "information kiosk", "wayfinding"],
    "Airport and Transport":  ["passenger kiosk", "check-in kiosk", "wayfinding terminal"],
    "Retail":                 ["digital signage", "self-service kiosk", "interactive display"],
    "Public Services":        ["citizen kiosk", "self-service terminal", "information kiosk"],
}


# ---------------------------------------------------------------------------
# Fields requested from TED
# ---------------------------------------------------------------------------

RETURN_FIELDS = [
    "publication-number",
    "TI",
    "buyer-name",
    "CY",
    "PD",
    "DT",
    "classification-cpv",
    "notice-type",
]


# ---------------------------------------------------------------------------
# MCP tool
# ---------------------------------------------------------------------------

@mcp.tool()
def ted_search(sector: str, time_range_days: int = 30) -> list[dict]:

    try:

        logger.info(f"ted_search — start — sector='{sector}' | days={time_range_days}")

        cpv_codes = SECTOR_CPV_MAP.get(sector, [])
        keywords = SECTOR_KEYWORDS.get(sector, [])

        date_from = (datetime.utcnow() - timedelta(days=time_range_days)).strftime("%Y%m%d")
        date_to = datetime.utcnow().strftime("%Y%m%d")

        results = []
        seen_ids = set()

        # --------------------------------------------------
        # CPV search
        # --------------------------------------------------

        if cpv_codes:

            cpv_terms = " OR ".join(
                f"classification-cpv = {cpv}" for cpv in cpv_codes
            )

            cpv_query = (
                f"({cpv_terms}) "
                f"AND publication-date >= {date_from} "
                f"AND publication-date <= {date_to}"
            )

            cpv_results = _run_query(cpv_query)

            for notice in cpv_results:

                parsed = _parse_notice(notice, sector, "cpv_match")

                if parsed and parsed["notice_id"] not in seen_ids:
                    seen_ids.add(parsed["notice_id"])
                    results.append(parsed)

        logger.info(f"ted_search — CPV search: {len(results)} results")

        # --------------------------------------------------
        # Keyword search
        # --------------------------------------------------

        if keywords:

            kw_terms = " OR ".join(f'FT ~ "{kw}"' for kw in keywords[:3])

            kw_query = (
                f"({kw_terms}) "
                f"AND publication-date >= {date_from} "
                f"AND publication-date <= {date_to}"
            )

            kw_results = _run_query(kw_query)

            for notice in kw_results:

                parsed = _parse_notice(notice, sector, "keyword_match")

                if parsed and parsed["notice_id"] not in seen_ids:
                    seen_ids.add(parsed["notice_id"])
                    results.append(parsed)

        logger.info(f"ted_search — total tenders returned: {len(results)}")

        return results

    except Exception as e:

        logger.error(f"ted_search error: {e}", exc_info=True)

        return []


# ---------------------------------------------------------------------------
# Query runner
# ---------------------------------------------------------------------------

def _run_query(query: str, max_results: int = 20) -> list[dict]:

    payload = {
        "query":  query,
        "fields": RETURN_FIELDS,
        "page":   1,
        "limit":  max_results,
    }

    try:

        response = requests.post(
            TED_SEARCH_URL,
            json=payload,
            timeout=20,
            headers={
            "Content-Type":  "application/json",
            "Accept":        "application/json",
            "Accept-Language": "en",
            },
        )

        if response.status_code == 200:

            data = json.loads(response.content.decode('utf-8'))
            return data.get("notices", [])

        logger.warning(f"TED HTTP {response.status_code}: {response.text[:200]}")
        return []

    except Exception as e:

        logger.error(f"TED query error: {e}")
        return []


# ---------------------------------------------------------------------------
# Notice parser
# ---------------------------------------------------------------------------

def _parse_notice(notice: dict, sector: str, match_type: str) -> dict | None:

    try:

        notice_id = notice.get("publication-number", "")
        title = _extract_text(notice.get("TI", ""))
        country = notice.get("CY", "")
        pub_date = notice.get("PD", "")
        deadline = notice.get("DT", "")
        authority = _extract_text(notice.get("buyer-name", ""))
        cpv_raw = notice.get("classification-cpv", [])

        # normalize country
        if isinstance(country, list):
            country = country[0] if country else ""

        # normalize deadline
        if isinstance(deadline, list) and deadline:
            deadline = deadline[0]

        # primary CPV
        primary_cpv = ""
        if isinstance(cpv_raw, list) and cpv_raw:
            primary_cpv = cpv_raw[0]

        if not notice_id:
            return None

        url = f"https://ted.europa.eu/en/notice/-/detail/{notice_id}"

        return {
            "notice_id": notice_id,
            "title": title,
            "country": country,
            "published_at": pub_date,
            "deadline": deadline,
            "authority": authority,
            "primary_cpv": primary_cpv,
            "cpv_codes": cpv_raw[:3] if isinstance(cpv_raw, list) else [],
            "url": url,
            "sector": sector,
            "match_type": match_type,
            "signal_type": "live_tender",
            "source": "ted.europa.eu",
            "source_type": "primary",
            "api_origin": "ted",
        }

    except Exception:

        return None


# ---------------------------------------------------------------------------
# Multilingual text extractor (improved)
# ---------------------------------------------------------------------------

def _extract_text(field) -> str:
    """
    Extracts text from TED multilingual fields.

    Handles:
    - strings
    - multilingual dicts (ENG / EN / en / other)
    - lists of dicts
    """

    if not field:
        return ""

    if isinstance(field, str):
        return field.strip()

    if isinstance(field, list):
        for item in field:
            text = _extract_text(item)
            if text:
                return text
        return ""

    if isinstance(field, dict):

        for key in ("ENG", "ENG_FULL", "EN", "en", "eng"):
            if key in field and isinstance(field[key], str):
                return field[key].strip()

        # fallback: return first non-empty string value
        # (translation will be handled by evaluate_opportunities)
        for value in field.values():
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""