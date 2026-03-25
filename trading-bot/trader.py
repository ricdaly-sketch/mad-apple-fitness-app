"""Trade execution and position management."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from config import MAX_POSITION_USDC, TAKE_PROFIT_EDGE
from strategy import Opportunity

log = logging.getLogger(__name__)


@dataclass
class Position:
    token_id: str
    market_question: str
    outcome: str
    entry_price: float
    size: float
    shares: float
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None

    @property
    def is_open(self) -> bool:
        return self.closed_at is None


class Trader:
    def __init__(self, client, paper: bool = True):
        self.client = client
        self.paper = paper
        self.positions: list[Position] = []
        self.realised_pnl: float = 0.0

    def open_position(self, opp: Opportunity) -> Optional[Position]:
        if self._already_holding(opp.token_id):
            return None

        if opp.market_price <= 0:
            log.warning(f"Skipping opportunity with invalid price {opp.market_price}")
            return None

        size = min(MAX_POSITION_USDC, opp.liquidity_usdc * 0.05)
        shares = size / opp.market_price

        try:
            self.client.place_order(
                token_id=opp.token_id,
                side="BUY",
                price=opp.market_price,
                size=size,
                paper=self.paper,
            )
        except Exception as exc:
            log.error(f"BUY order failed for {opp.token_id}: {exc}")
            return None

        tag = "[PAPER]" if self.paper else "[LIVE]"
        log.info(
            f"{tag} BUY  {opp.outcome:4s} @ {opp.market_price:.3f} "
            f"| fair={opp.fair_prob:.3f} edge={opp.edge:.3f} "
            f"| ${size:.2f} -> {shares:.1f} shares "
            f"| {opp.market_question[:60]}"
        )

        pos = Position(
            token_id=opp.token_id,
            market_question=opp.market_question,
            outcome=opp.outcome,
            entry_price=opp.market_price,
            size=size,
            shares=shares,
        )
        self.positions.append(pos)
        return pos

    def check_and_close_positions(self, current_prices: dict[str, float]) -> None:
        for pos in self.positions:
            if not pos.is_open:
                continue
            current_price = current_prices.get(pos.token_id)
            if current_price is None:
                continue
            edge_remaining = current_price - pos.entry_price
            if edge_remaining <= TAKE_PROFIT_EDGE:
                self._close_position(pos, current_price)

    def _close_position(self, pos: Position, exit_price: float) -> None:
        try:
            self.client.place_order(
                token_id=pos.token_id,
                side="SELL",
                price=exit_price,
                size=pos.shares,
                paper=self.paper,
            )
        except Exception as exc:
            log.error(f"SELL order failed for {pos.token_id}: {exc} — position remains open")
            return  # Do NOT mark closed if the order failed

        pos.exit_price = exit_price
        pos.closed_at = datetime.utcnow()
        pnl = (exit_price - pos.entry_price) * pos.shares
        pos.pnl = round(pnl, 4)
        self.realised_pnl += pnl

        tag = "[PAPER]" if self.paper else "[LIVE]"
        log.info(
            f"{tag} SELL {pos.outcome:4s} @ {exit_price:.3f} "
            f"| entry={pos.entry_price:.3f} pnl=${pnl:+.2f} "
            f"| total_pnl=${self.realised_pnl:+.2f} "
            f"| {pos.market_question[:60]}"
        )

    def _already_holding(self, token_id: str) -> bool:
        return any(p.token_id == token_id and p.is_open for p in self.positions)

    def summary(self) -> str:
        open_count = sum(1 for p in self.positions if p.is_open)
        total_trades = len(self.positions)
        wins = sum(1 for p in self.positions if p.pnl and p.pnl > 0)
        win_rate = wins / (total_trades - open_count) * 100 if total_trades > open_count else 0
        return (
            f"Trades={total_trades} | Open={open_count} "
            f"| Win rate={win_rate:.0f}% "
            f"| Realised PnL=${self.realised_pnl:+.2f}"
        )
