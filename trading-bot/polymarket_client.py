"""Thin wrapper around the Polymarket CLOB REST API."""

import time
import requests
from typing import Optional
from config import CLOB_BASE_URL, MAX_LATENCY_MS


class PolymarketClient:
    def __init__(self, api_key: str, wallet_address: str):
        if not api_key:
            raise ValueError(
                "POLY_API_KEY must be set. Check your .env file."
            )
        if not wallet_address:
            raise ValueError(
                "POLY_WALLET_ADDRESS must be set. Check your .env file."
            )
        self._api_key = api_key
        self._wallet_address = wallet_address
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        t0 = time.monotonic()
        resp = self.session.get(f"{CLOB_BASE_URL}{path}", params=params, timeout=5)
        latency_ms = (time.monotonic() - t0) * 1000
        resp.raise_for_status()
        if latency_ms > MAX_LATENCY_MS:
            raise RuntimeError(f"Latency {latency_ms:.0f}ms exceeds limit of {MAX_LATENCY_MS}ms")
        return resp.json()

    def get_markets(self, next_cursor: str = "") -> dict:
        """Fetch paginated list of active markets."""
        params = {"next_cursor": next_cursor} if next_cursor else {}
        return self._get("/markets", params=params)

    def get_orderbook(self, token_id: str) -> dict:
        """Fetch best bid/ask for a token."""
        return self._get("/book", params={"token_id": token_id})

    def place_order(self, token_id: str, side: str, price: float,
                    size: float, paper: bool = True) -> dict:
        """Place a limit order. In paper mode, simulates the order."""
        if paper:
            return {
                "paper": True,
                "token_id": token_id,
                "side": side,
                "price": price,
                "size": size,
                "status": "SIMULATED",
            }
        payload = {
            "token_id": token_id,
            "price": price,
            "size": size,
            "side": side,
            "type": "GTC",
            "maker_address": self._wallet_address,
        }
        resp = self.session.post(f"{CLOB_BASE_URL}/order", json=payload, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") not in ("matched", "live", "delayed"):
            raise RuntimeError(f"Order rejected by exchange: {data}")
        return data

    def get_balance(self) -> float:
        """Return available USDC balance."""
        data = self._get("/balance")
        try:
            return float(data["balance"])
        except (KeyError, ValueError, TypeError) as e:
            raise RuntimeError(f"Unexpected balance response: {data}") from e
