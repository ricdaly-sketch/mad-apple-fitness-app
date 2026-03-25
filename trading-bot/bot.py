"""Main entry point for the Polymarket arbitrage bot with rich terminal UI."""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from config import SCAN_INTERVAL_S
from polymarket_client import PolymarketClient
from strategy import find_opportunities
from trader import Trader

console = Console()
MAX_PAGINATION_PAGES = 100
MAX_LOG_LINES = 12

log_lines: list[str] = []


class UIHandler(logging.Handler):
    """Captures log records into an in-memory list for the dashboard."""
    def emit(self, record: logging.LogRecord) -> None:
        level = record.levelname
        msg = self.format(record)
        colors = {"INFO": "green", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "bold red"}
        color = colors.get(level, "white")
        log_lines.append(f"[{color}]{msg}[/{color}]")
        if len(log_lines) > MAX_LOG_LINES:
            log_lines.pop(0)


def setup_logging() -> None:
    handler = UIHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                                           datefmt="%H:%M:%S"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def fetch_all_markets(client: PolymarketClient) -> list[dict]:
    markets = []
    cursor = ""
    for _ in range(MAX_PAGINATION_PAGES):
        page = client.get_markets(next_cursor=cursor)
        markets.extend(page.get("data", []))
        cursor = page.get("next_cursor", "")
        if not cursor or cursor == "LTE=":
            break
    return markets


def build_layout(trader: Trader, scan: int, mode: str,
                 latest_opps: list, markets_count: int) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="logs", size=MAX_LOG_LINES + 2),
    )
    layout["body"].split_row(
        Layout(name="positions"),
        Layout(name="opportunities"),
    )

    # ── Header ──────────────────────────────────────────────────────────
    pnl = trader.realised_pnl
    pnl_color = "green" if pnl >= 0 else "red"
    open_pos = sum(1 for p in trader.positions if p.is_open)
    header_text = Text(justify="center")
    header_text.append(" POLYMARKET ARB BOT ", style="bold white on dark_blue")
    header_text.append(f"  mode={mode}  ", style="bold cyan")
    header_text.append(f"scan=#{scan}  ", style="dim")
    header_text.append(f"markets={markets_count}  ", style="dim")
    header_text.append(f"PnL=${pnl:+.2f}", style=f"bold {pnl_color}")
    layout["header"].update(Panel(header_text, box=box.HORIZONTALS))

    # ── Open Positions ───────────────────────────────────────────────────
    pos_table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta",
                      expand=True)
    pos_table.add_column("Market", style="white", no_wrap=False, ratio=5)
    pos_table.add_column("Side", justify="center", ratio=1)
    pos_table.add_column("Entry", justify="right", ratio=1)
    pos_table.add_column("Size", justify="right", ratio=1)
    pos_table.add_column("Opened", justify="right", ratio=2)

    open_positions = [p for p in trader.positions if p.is_open]
    if open_positions:
        for p in open_positions:
            pos_table.add_row(
                p.market_question[:45],
                f"[cyan]{p.outcome}[/cyan]",
                f"{p.entry_price:.3f}",
                f"${p.size:.2f}",
                p.opened_at.strftime("%H:%M:%S"),
            )
    else:
        pos_table.add_row("[dim]No open positions[/dim]", "", "", "", "")

    layout["positions"].update(
        Panel(pos_table, title=f"[bold]Open Positions ({open_pos})[/bold]", box=box.ROUNDED)
    )

    # ── Latest Opportunities ─────────────────────────────────────────────
    opp_table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta",
                      expand=True)
    opp_table.add_column("Market", ratio=5)
    opp_table.add_column("Side", justify="center", ratio=1)
    opp_table.add_column("Price", justify="right", ratio=1)
    opp_table.add_column("Fair", justify="right", ratio=1)
    opp_table.add_column("Edge", justify="right", ratio=1)

    if latest_opps:
        for opp in latest_opps[:8]:
            edge_color = "bright_green" if opp.edge > 0.05 else "yellow"
            opp_table.add_row(
                opp.market_question[:45],
                f"[cyan]{opp.outcome}[/cyan]",
                f"{opp.market_price:.3f}",
                f"{opp.fair_prob:.3f}",
                f"[{edge_color}]+{opp.edge:.3f}[/{edge_color}]",
            )
    else:
        opp_table.add_row("[dim]Scanning...[/dim]", "", "", "", "")

    wins = sum(1 for p in trader.positions if p.pnl and p.pnl > 0)
    closed = sum(1 for p in trader.positions if not p.is_open)
    win_rate = f"{wins}/{closed}" if closed else "--"
    layout["opportunities"].update(
        Panel(opp_table,
              title=f"[bold]Opportunities Found | Trades={len(trader.positions)} Win={win_rate}[/bold]",
              box=box.ROUNDED)
    )

    # ── Logs ─────────────────────────────────────────────────────────────
    log_text = Text()
    for line in log_lines:
        log_text.append_text(Text.from_markup(line + "\n"))
    layout["logs"].update(Panel(log_text, title="[bold]Logs[/bold]", box=box.ROUNDED))

    return layout


def main() -> None:
    parser = argparse.ArgumentParser(description="Polymarket Arbitrage Bot")
    parser.add_argument("--paper", action="store_true", default=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    paper_mode = not args.live
    load_dotenv()
    setup_logging()
    log = logging.getLogger(__name__)

    if not paper_mode:
        missing = [k for k in ("POLY_API_KEY", "POLY_WALLET_ADDRESS", "PRIVATE_KEY")
                   if not os.getenv(k)]
        if missing:
            console.print(f"[bold red]Live mode requires: {missing}[/bold red]")
            sys.exit(1)

    try:
        client = PolymarketClient(
            api_key=os.getenv("POLY_API_KEY", ""),
            wallet_address=os.getenv("POLY_WALLET_ADDRESS", ""),
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        sys.exit(1)

    trader = Trader(client, paper=paper_mode)
    mode_label = "PAPER" if paper_mode else "LIVE"
    scan_count = 0
    latest_opps = []
    markets_count = 0

    log.info(f"Bot started | mode={mode_label} | interval={SCAN_INTERVAL_S}s")

    with Live(build_layout(trader, scan_count, mode_label, latest_opps, markets_count),
              refresh_per_second=2, screen=True) as live:
        while True:
            scan_count += 1
            try:
                markets = fetch_all_markets(client)
                markets_count = len(markets)
                log.info(f"Scan #{scan_count}: loaded {markets_count} markets")

                orderbooks: dict[str, dict] = {}
                for market in markets:
                    for token in market.get("tokens", []):
                        token_id = token.get("token_id")
                        if token_id:
                            try:
                                orderbooks[token_id] = client.get_orderbook(token_id)
                            except Exception:
                                pass

                latest_opps = find_opportunities(markets, orderbooks)

                if latest_opps:
                    log.info(f"Found {len(latest_opps)} arbitrage windows")
                    for opp in latest_opps:
                        trader.open_position(opp)
                else:
                    log.info("No opportunities above min edge")

                current_prices: dict[str, float] = {}
                for tid, book in orderbooks.items():
                    bids = book.get("bids") or []
                    if bids:
                        try:
                            current_prices[tid] = float(bids[0]["price"])
                        except (KeyError, ValueError, TypeError):
                            pass
                trader.check_and_close_positions(current_prices)

            except KeyboardInterrupt:
                break
            except Exception as exc:
                log.error(f"Scan error: {exc}")

            live.update(build_layout(trader, scan_count, mode_label, latest_opps, markets_count))
            time.sleep(SCAN_INTERVAL_S)

    console.print(f"\n[bold]Final: {trader.summary()}[/bold]")


if __name__ == "__main__":
    main()
