import time
from pathlib import Path
from threading import Lock, Thread
from typing import Optional

import requests

from appkit.base import Application, Scene
from appkit.graphics_helpers import Color, Font, draw_text


class TickerData:
    def __init__(self):
        self.tickers = {}
        self.lock = Lock()
        self.last_update = 0

    def update_ticker(self, symbol: str, is_crypto: bool = False):
        try:
            if is_crypto:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
                response = requests.get(url, timeout=5)
                data = response.json()

                if symbol in data:
                    price = data[symbol]["usd"]
                    change = data[symbol].get("usd_24h_change", 0)

                    with self.lock:
                        self.tickers[symbol] = {
                            "price": price,
                            "change": change,
                            "is_crypto": True,
                        }
            else:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                response = requests.get(url, headers=headers, timeout=5)

                if response.status_code != 200:
                    print(
                        f"Yahoo Finance returned status {response.status_code} for {symbol}"
                    )
                    return

                data = response.json()

                if (
                    "chart" in data
                    and "result" in data["chart"]
                    and len(data["chart"]["result"]) > 0
                ):
                    result = data["chart"]["result"][0]
                    meta = result["meta"]
                    price = meta["regularMarketPrice"]
                    prev_close = meta["chartPreviousClose"]
                    change = ((price - prev_close) / prev_close) * 100

                    with self.lock:
                        self.tickers[symbol] = {
                            "price": price,
                            "change": change,
                            "is_crypto": False,
                        }
        except Exception as e:
            print(f"Error updating {symbol}: {e}")

    def get_ticker(self, symbol: str):
        with self.lock:
            return self.tickers.get(symbol)


class TickerScene(Scene):
    def __init__(self, config, app_dir: Path):
        self.config = config
        self.app_dir = app_dir
        font_path = app_dir / "resources" / "5x7.bdf"
        self.font = Font(str(font_path))
        self.ticker_data = TickerData()
        self.current_index = 0
        self.update_thread = None
        self.running = True
        self.last_switch = time.time()

        self.start_updates()

    def start_updates(self):
        self.update_thread = Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def _update_loop(self):
        while self.running:
            symbols = self.config.get("symbols", [])
            crypto_symbols = self.config.get("crypto_symbols", [])

            for symbol in symbols:
                self.ticker_data.update_ticker(symbol, is_crypto=False)

            for symbol in crypto_symbols:
                self.ticker_data.update_ticker(symbol, is_crypto=True)

            time.sleep(60)

    def render(self, canvas) -> None:
        canvas.Clear()

        symbols = self.config.get("symbols", [])
        crypto_symbols = self.config.get("crypto_symbols", [])
        all_symbols = [(s, False) for s in symbols] + [
            (s, True) for s in crypto_symbols
        ]

        if not all_symbols:
            draw_text(canvas, self.font, 2, 10, Color(255, 255, 255), "No tickers")
            return

        if self.current_index >= len(all_symbols):
            self.current_index = 0

        symbol, is_crypto = all_symbols[self.current_index]
        data = self.ticker_data.get_ticker(symbol)

        if data:
            display_symbol = symbol.upper()
            price = data["price"]
            change = data["change"]

            if price >= 1000:
                price_str = f"${price:,.0f}"
            elif price >= 1:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.4f}"

            change_str = f"{change:+.2f}%"

            if change >= 0:
                color = Color(0, 255, 0)
            else:
                color = Color(255, 0, 0)

            draw_text(canvas, self.font, 2, 8, Color(255, 255, 255), display_symbol)
            draw_text(canvas, self.font, 2, 16, color, price_str)
            draw_text(canvas, self.font, 2, 24, color, change_str)

            if time.time() - self.last_switch > 3:
                self.current_index = (self.current_index + 1) % len(all_symbols)
                self.last_switch = time.time()
        else:
            draw_text(canvas, self.font, 2, 16, Color(255, 255, 0), f"Loading...")

    def handle_input(self, input_type: str) -> Optional[str]:
        if input_type == "cancel":
            self.running = False
            return "menu"
        elif input_type == "right":
            symbols = self.config.get("symbols", [])
            crypto_symbols = self.config.get("crypto_symbols", [])
            all_symbols = [(s, False) for s in symbols] + [
                (s, True) for s in crypto_symbols
            ]
            self.current_index = (self.current_index + 1) % len(all_symbols)
            self.last_switch = time.time()
        elif input_type == "left":
            symbols = self.config.get("symbols", [])
            crypto_symbols = self.config.get("crypto_symbols", [])
            all_symbols = [(s, False) for s in symbols] + [
                (s, True) for s in crypto_symbols
            ]
            self.current_index = (self.current_index - 1) % len(all_symbols)
            self.last_switch = time.time()
        return None


class App(Application):
    def on_config_changed(self):
        return

    def get_framerate(self) -> int:
        return 10

    def default_scene(self) -> Scene:
        return TickerScene(self.config, self.app_dir)

    def get_active_scene(self) -> Scene:
        return TickerScene(self.config, self.app_dir)

    def get_scenes(self):
        return {"ticker": TickerScene(self.config, self.app_dir)}
