"""Arbitrage / mispricing detection strategy."""

from dataclasses import dataclass
from typing import Optional
from config import MIN_EDGE, MIN_LIQUIDITY_USDC


@dataclass
class Opportunity:
    market_id: str
    market_question: str
    token_id: str
    outcome: str
    market_price: float      # Current best ask on Polymarket
    fair_prob: float         # Our estimated fair probability
    edge: float              # fair_prob - market_price
    liquidity_usdc: float


def estimate_fair_probability(market: dict, outcome: str) -> Optional[float]:
    """
    Estimate fair probability for an outcome.

    This is the core alpha-generation logic. A real implementation
    would use:
      - External data feeds (news, polls, resolution criteria)
      - ML models trained on historical market data
      - Complementary market prices (correlated markets)

    For now we use the simple heuristic: if both YES and NO tokens
    are trading, the sum should be ~1.0. If it deviates, one side
    is mispriced. We use the complement of the opposing token price.
    """
    outcomes = market.get("tokens", [])
    if len(outcomes) != 2:
        return None

    prices = {t["outcome"]: float(t.get("price", 0)) for t in outcomes}
    yes_price = prices.get("Yes", prices.get("YES", None))
    no_price = prices.get("No", prices.get("NO", None))

    if yes_price is None or no_price is None:
        return None

    total = yes_price + no_price
    if total <= 0:
        return None

    # Normalise: if sum != 1, markets are mispriced relative to each other
    if outcome in ("Yes", "YES"):
        return 1.0 - no_price   # implied fair YES prob
    else:
        return 1.0 - yes_price  # implied fair NO prob


def find_opportunities(markets: list[dict], orderbooks: dict[str, dict]) -> list[Opportunity]:
    """Scan markets and return a ranked list of trading opportunities."""
    opportunities = []

    for market in markets:
        if market.get("closed") or not market.get("active"):
            continue

        liquidity = float(market.get("volume", 0))
        if liquidity < MIN_LIQUIDITY_USDC:
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
                    market_id=market["condition_id"],
                    market_question=market.get("question", ""),
                    token_id=token_id,
                    outcome=outcome,
                    market_price=best_ask,
                    fair_prob=round(fair_prob, 4),
                    edge=round(edge, 4),
                    liquidity_usdc=liquidity,
                ))

    # Rank by edge descending
    return sorted(opportunities, key=lambda o: o.edge, reverse=True)


def _best_ask(book: dict) -> Optional[float]:
    asks = book.get("asks", [])
    if not asks:
        return None
    return float(min(asks, key=lambda a: float(a["price"]))["price"])
