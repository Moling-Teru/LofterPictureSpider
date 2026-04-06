# -*- coding: utf-8 -*-
"""Concurrent-safe downloader with queue-based log writer."""

from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Optional

try:
    from .api import build_session
except ImportError:
    from api import build_session


class AsyncLineLogger:
    """Single writer thread to avoid concurrent file append contention."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._queue: queue.Queue[str] = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._writer, daemon=True)
        self._thread.start()

    def _writer(self) -> None:
        with open(self.file_path, "a", encoding="utf-8") as f:
            while not self._stop.is_set() or not self._queue.empty():
                try:
                    line = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                f.write(line)
                self._queue.task_done()

    def write_line(self, message: str) -> None:
        self._queue.put(message.rstrip("\n") + "\n")

    def close(self) -> None:
        self._queue.join()
        self._stop.set()
        self._thread.join(timeout=2)


class Downloader:
    IMAGE_HEADERS = {
        "User-Agent": "Reqable/2.21.1",
        "accept-encoding": "gzip",
    }

    VIDEO_HEADERS = {
        "User-Agent": "Reqable/2.33.12",
        "accept-encoding": "gzip",
    }

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.session = build_session(max_retries=3, pool_size=16)

    @staticmethod
    def _normalize_image_url(url: str) -> str:
        if not (
            url.startswith("https://nos.netease.com/")
            or url.startswith("http://nos.netease.com/")
        ):
            return url

        # URL shape: scheme://nos.netease.com/{bucket}/{path...}
        parts = url.split("/", 4)
        if len(parts) < 4:
            return url

        address = parts[3]
        suffix = parts[4] if len(parts) > 4 else ""
        new_base = f"https://{address}.lf127.net"
        return f"{new_base}/{suffix}" if suffix else new_base

    def download_image(self, url: str, save_path: Path, proxy: Optional[dict[str, str]] = None) -> None:
        normalized = self._normalize_image_url(url)
        response = self.session.get(
            normalized,
            timeout=self.timeout,
            headers=self.IMAGE_HEADERS,
            params={"type": "png"},
            proxies=proxy,
        )
        response.raise_for_status()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)

    def download_video(self, url: str, save_path: Path, proxy: Optional[dict[str, str]] = None) -> None:
        response = self.session.get(
            url,
            timeout=self.timeout,
            headers=self.VIDEO_HEADERS,
            proxies=proxy,
        )
        response.raise_for_status()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)

    def save_text_html(self, content: str, save_path: Path, title: str) -> None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        # Keep content unescaped to preserve original LOFTER HTML fragments.
        doc = (
            "<!doctype html>\n"
            "<html>\n"
            "  <head>\n"
            "    <meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\" />\n"
            f"    <title>{title}</title>\n"
            "  </head>\n"
            "  <body>\n"
            "    <div id=\"payWarningDiv\"><h2 id=\"PayWarning\">"
            "Content may be incomplete for paid posts.</h2></div>\n"
            "    <div id=\"postContentDiv\">"
            "<p id=\"postContent\" style=\"font-size: 16px; line-height: 1.6;\">"
            f"{content}</p></div>\n"
            "  </body>\n"
            "</html>\n"
        )

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(doc)
