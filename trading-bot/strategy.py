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
    try:
        result = float(value)
        if not (0 < result <= 1):
            return None
        return result
    except (TypeError, ValueError):
        return None


def estimate_fair_probability(market: dict, outcome: str) -> Optional[float]:
    tokens = market.get("tokens", [])
    if len(tokens) != 2:
        return None

    prices = {}
    for t in tokens:
        price = _safe_price(t.get("price"))
        if price is not None:
            prices[t.get("outcome", "")] = price

    yes_price = prices.get("Yes", prices.get("YES"))
    no_price = prices.get("No", prices.get("NO"))

    if yes_price is None or no_price is None:
        return None

    fair = (1.0 - no_price) if outcome in ("Yes", "YES") else (1.0 - yes_price)

    if not (0 < fair <= 1):
        return None
    return fair


def find_opportunities(markets: list[dict]) -> list["Opportunity"]:
    """Scan markets using embedded token prices."""
    opportunities = []
    skipped_liquidity = 0
    skipped_price = 0
    checked = 0

    for market in markets:
        if market.get("closed") or not market.get("active"):
            continue

        try:
            liquidity = float(market.get("volume", 0))
        except (TypeError, ValueError):
            continue

        if liquidity < MIN_LIQUIDITY_USDC:
            skipped_liquidity += 1
            continue

        condition_id = market.get("condition_id")
        if not condition_id:
            continue

        for token in market.get("tokens", []):
            token_id = token.get("token_id")
            outcome = token.get("outcome", "")
            if not token_id:
                continue

            market_price = _safe_price(token.get("price"))
            if market_price is None:
                skipped_price += 1
                continue

            fair_prob = estimate_fair_probability(market, outcome)
            if fair_prob is None:
                continue

            checked += 1
            edge = fair_prob - market_price
            if edge >= MIN_EDGE:
                opportunities.append(Opportunity(
                    market_id=condition_id,
                    market_question=market.get("question", ""),
                    token_id=token_id,
                    outcome=outcome,
                    market_price=market_price,
                    fair_prob=round(fair_prob, 4),
                    edge=round(edge, 4),
                    liquidity_usdc=liquidity,
                ))

    log.info(
        f"Checked {checked} tokens | skipped low-liquidity={skipped_liquidity} "
        f"no-price={skipped_price} | found {len(opportunities)} opportunities"
    )
    return sorted(opportunities, key=lambda o: o.edge, reverse=True)
