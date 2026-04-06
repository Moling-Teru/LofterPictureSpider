# -*- coding: utf-8 -*-
"""Thread-safe proxy pool with short-term cache."""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path
from typing import Optional

import requests


class ProxyPool:
    def __init__(
        self,
        proxy_api_file: Path,
        *,
        fetch_batch_size: int = 5,
        cache_ttl_seconds: int = 30,
        timeout: int = 5,
    ) -> None:
        self.proxy_api_file = proxy_api_file
        self.fetch_batch_size = max(1, fetch_batch_size)
        self.cache_ttl_seconds = max(1, cache_ttl_seconds)
        self.timeout = timeout

        self._lock = threading.Lock()
        self._proxy_token: Optional[str] = None
        self._pool: deque[dict[str, str]] = deque()
        self._last_fetch_at: float = 0.0

    def _read_proxy_token(self) -> str:
        if self._proxy_token is not None:
            return self._proxy_token

        with open(self.proxy_api_file, "r", encoding="utf-8") as f:
            token = f.read().strip()

        if not token:
            raise ValueError("proxy_api.txt is empty")

        self._proxy_token = token
        return token

    def _fetch_proxies(self, num: int) -> list[dict[str, str]]:
        token = self._read_proxy_token()
        url = (
            "https://api.douyadaili.com/proxy/?service=GetIp"
            f"&authkey={token}&num={num}&lifetime=15&prot=1&format=json"
        )
        response = requests.get(url, headers={"Connection": "Close"}, timeout=self.timeout)
        response.raise_for_status()

        payload = response.json()
        proxies: list[dict[str, str]] = []
        for item in payload.get("data", []):
            ip = item.get("ip")
            port = item.get("port")
            if not ip or not port:
                continue
            proxy = {
                "http": f"http://{ip}:{port}",
                "https": f"http://{ip}:{port}",
            }
            proxies.append(proxy)
        return proxies

    def _refresh_if_needed(self) -> None:
        now = time.time()
        need_refresh = (not self._pool) or (now - self._last_fetch_at > self.cache_ttl_seconds)
        if not need_refresh:
            return

        fetched = self._fetch_proxies(self.fetch_batch_size)
        self._pool.clear()
        self._pool.extend(fetched)
        self._last_fetch_at = now

    def get_proxies(self, num: int = 1, use_proxy: bool = False) -> list[Optional[dict[str, str]]]:
        if not use_proxy:
            return [None]

        with self._lock:
            try:
                self._refresh_if_needed()
            except (OSError, requests.RequestException, ValueError, json.JSONDecodeError):
                return [None]

            if not self._pool:
                return [None]

            count = max(1, num)
            result: list[Optional[dict[str, str]]] = []
            for _ in range(count):
                proxy = self._pool[0]
                self._pool.rotate(-1)
                result.append(proxy)
            return result
