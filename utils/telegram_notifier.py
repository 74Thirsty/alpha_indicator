"""Minimal Telegram messaging utility used by Alpha Indicator."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests


logger = logging.getLogger(__name__)


@dataclass
class TelegramNotifier:
    bot_token: str
    chat_id: str

    def send_message(self, message: str) -> bool:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}
        try:
            response = requests.post(url, data=payload, timeout=10)
            if not response.ok:
                logger.warning("Telegram API returned non-200 status: %s", response.text)
            return response.ok
        except requests.RequestException as exc:  # pragma: no cover - best effort logging
            logger.error("Telegram send failed: %s", exc)
            return False
