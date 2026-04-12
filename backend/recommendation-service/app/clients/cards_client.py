"""
Async client for the cards-service.

Fetches the full card catalogue from GET /api/v1/cards.
The recommend endpoint calls this once per request; the cards-service
owns the Neon Postgres DB and refreshes it weekly via Cloud Scheduler.
"""

import asyncio
import logging

import httpx

from app.models.card import Card

logger = logging.getLogger(__name__)


class CardsServiceError(Exception):
    """Raised when the cards-service returns an unexpected response."""


async def fetch_all_cards(client: httpx.AsyncClient, base_url: str) -> list[Card]:
    """
    Fetch every active card from the cards-service catalogue endpoint.

    Args:
        client:   Shared httpx.AsyncClient (stored on app.state).
        base_url: URL of the cards-service, e.g. https://walletace-cards-xxx.run.app

    Returns:
        List of Card objects ready for Phase 1 eligibility filtering.

    Raises:
        CardsServiceError: if the HTTP call fails or the payload is malformed.
    """
    try:
        response = await client.get(f"{base_url}/api/v1/cards", timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise CardsServiceError(
            f"Cards service returned {exc.response.status_code}"
        ) from exc
    except httpx.RequestError as exc:
        raise CardsServiceError(f"Cards service unreachable: {exc}") from exc

    try:
        payload = response.json()
        # Accepts both a plain list and {"cards": [...]} envelope
        raw_cards = payload if isinstance(payload, list) else payload["cards"]
        return [Card(**card) for card in raw_cards]
    except Exception as exc:
        raise CardsServiceError(f"Failed to parse cards response: {exc}") from exc


async def store_survey_response(
    client: httpx.AsyncClient,
    base_url: str,
    payload: dict,
) -> None:
    """
    Fire-and-forget: persist the survey + recommendation to cards-service.
    Errors are logged but never raised — storage must not block the response.
    """
    try:
        await asyncio.wait_for(
            client.post(f"{base_url}/api/v1/survey-responses", json=payload, timeout=5.0),
            timeout=5.0,
        )
    except Exception:
        logger.warning("Failed to store survey response", exc_info=True)
