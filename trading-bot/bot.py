"""Main entry point for the Polymarket arbitrage bot."""

import argparse
import logging
import os
import sys
import time
from dotenv import load_dotenv
import colorlog

from config import SCAN_INTERVAL_S
from polymarket_client import PolymarketClient
from strategy import find_opportunities
from trader import Trader

MAX_PAGINATION_PAGES = 100


def setup_logging() -> None:
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S UTC",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    ))
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Polymarket Arbitrage Bot")
    parser.add_argument("--paper", action="store_true", default=True,
                        help="Run in paper trading mode (default)")
    parser.add_argument("--live", action="store_true",
                        help="Run with real money (requires credentials)")
    args = parser.parse_args()

    paper_mode = not args.live
    load_dotenv()

    setup_logging()
    log = logging.getLogger(__name__)

    if not paper_mode:
        missing = [k for k in ("POLY_API_KEY", "POLY_WALLET_ADDRESS", "PRIVATE_KEY")
                   if not os.getenv(k)]
        if missing:
            log.critical(f"Live mode requires these env vars: {missing}")
            sys.exit(1)

    try:
        client = PolymarketClient(
            api_key=os.getenv("POLY_API_KEY", ""),
            wallet_address=os.getenv("POLY_WALLET_ADDRESS", ""),
        )
    except ValueError as exc:
        log.critical(str(exc))
        sys.exit(1)

    trader = Trader(client, paper=paper_mode)

    mode_label = "PAPER" if paper_mode else "LIVE"
    log.info(f"=== Polymarket Arb Bot starting | mode={mode_label} ===")
    log.info(f"Scanning every {SCAN_INTERVAL_S}s | min_edge=0.03 | max_latency=30ms")

    scan_count = 0
    while True:
        scan_count += 1
        try:
            log.info(f"--- Scan #{scan_count}: fetching markets ---")
            markets = fetch_all_markets(client)
            log.info(f"Loaded {len(markets)} active markets")

            orderbooks: dict[str, dict] = {}
            for market in markets:
                for token in market.get("tokens", []):
                    token_id = token.get("token_id")
                    if token_id:
                        try:
                            orderbooks[token_id] = client.get_orderbook(token_id)
                        except Exception:
                            pass

            opportunities = find_opportunities(markets, orderbooks)

            if opportunities:
                log.info(f"Found {len(opportunities)} arbitrage windows - executing high-confidence trades")
                for opp in opportunities:
                    trader.open_position(opp)
            else:
                log.info("No opportunities above min edge threshold")

            current_prices: dict[str, float] = {}
            for tid, book in orderbooks.items():
                bids = book.get("bids") or []
                if bids:
                    try:
                        current_prices[tid] = float(bids[0]["price"])
                    except (KeyError, ValueError, TypeError):
                        pass
            trader.check_and_close_positions(current_prices)

            log.info(trader.summary())

        except KeyboardInterrupt:
            log.info("Shutting down...")
            log.info(trader.summary())
            break
        except Exception as exc:
            log.error(f"Scan error: {exc}")

        time.sleep(SCAN_INTERVAL_S)


if __name__ == "__main__":
    main()
