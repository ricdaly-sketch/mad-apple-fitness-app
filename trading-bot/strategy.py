"""Arbitrage / mispricing detection strategy."""

import logging
from dataclasses import dataclass
from typing import Optional
from config import MIN_EDGE, MIN_LIQUIDITY_USDC

log = logging.getLogger(__name__)


@dataclass
class Opportunity:
    market_id: str
    market_question: str
    token_id: str
    outcome: str
    market_price: float
    fair_prob: float
    edge: float
    liquidity_usdc: float


def _safe_price(value) -> Optional[float]:
    """Parse a price from untrusted API data. Must be in (0, 1]."""
    try:
        result = float(value)
        if not (0 < result <= 1):
            return None
        return result
    except (TypeError, ValueError):
        return None


def estimate_fair_probability(market: dict, outcome: str) -> Optional[float]:
    outcomes = market.get("tokens", [])
    if len(outcomes) != 2:
        return None

    prices = {}
    for t in outcomes:
        price = _safe_price(t.get("price"))
        if price is not None:
            prices[t.get("outcome", "")] = price

    yes_price = prices.get("Yes", prices.get("YES"))
    no_price = prices.get("No", prices.get("NO"))

    if yes_price is None or no_price is None:
        return None

    if outcome in ("Yes", "YES"):
        fair = 1.0 - no_price
    else:
        fair = 1.0 - yes_price

    if not (0 < fair <= 1):
        return None
    return fair


def find_opportunities(markets: list[dict], orderbooks: dict[str, dict]) -> list[Opportunity]:
    """Scan markets and return a ranked list of trading opportunities."""
    opportunities = []

    for market in markets:
        if market.get("closed") or not market.get("active"):
            continue

        try:
            liquidity = float(market.get("volume", 0))
        except (TypeError, ValueError):
            continue
        if liquidity < MIN_LIQUIDITY_USDC:
            continue

        condition_id = market.get("condition_id")
        if not condition_id:
            continue

        for token in market.get("tokens", []):
            token_id = token.get("token_id")
            outcome = token.get("outcome", "")
            if not token_id:
                continue

            book = orderbooks.get(token_id, {})
            best_ask = _best_ask(book)
            if best_ask is None:
                continue

            fair_prob = estimate_fair_probability(market, outcome)
            if fair_prob is None:
                continue

            edge = fair_prob - best_ask
            if edge >= MIN_EDGE:
                opportunities.append(Opportunity(
                    market_id=condition_id,
                    market_question=market.get("question", ""),
                    token_id=token_id,
                    outcome=outcome,
                    market_price=best_ask,
                    fair_prob=round(fair_prob, 4),
                    edge=round(edge, 4),
                    liquidity_usdc=liquidity,
                ))

    return sorted(opportunities, key=lambda o: o.edge, reverse=True)


def _best_ask(book: dict) -> Optional[float]:
    asks = book.get("asks", [])
    if not asks:
        return None
    try:
        price = float(min(asks, key=lambda a: float(a["price"]))["price"])
    except (TypeError, ValueError, KeyError):
        return None
    if not (0 < price <= 1):
        return None
    return price
