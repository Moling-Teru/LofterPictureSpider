# -*- coding: utf-8 -*-
"""Configuration and path helpers for NewTags."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DEFAULT_CONTENTS_ROOT = BASE_DIR / "Contents"
DEFAULT_PROXY_API_PATH = BASE_DIR / "proxy_api.txt"


@dataclass(frozen=True)
class TimeRange:
    start_ts: str
    end_ts: str
    recent_day: str


def load_config(config_path: Optional[Path] = None) -> dict[str, Any]:
    path = config_path or CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("config.yaml root must be a mapping")
    return data


class Config:
    """Typed config access with sane defaults."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._raw = load_config(config_path)

    @property
    def tag(self) -> str:
        return str(self._raw.get("tag", "")).strip()

    @property
    def post_type(self) -> str:
        return str(self._raw.get("type", "date")).strip()

    @property
    def turn(self) -> Optional[list[int]]:
        value = self._raw.get("turn")
        if value is None:
            return None
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("turn must be a list like [start, end]")
        return [int(value[0]), int(value[1])]

    @property
    def specified(self) -> Optional[list[int]]:
        value = self._raw.get("specified")
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("specified must be a list of integers")
        return [int(v) for v in value]

    @property
    def likes(self) -> Optional[int]:
        value = self._raw.get("likes")
        if value in (None, ""):
            return None
        return int(value)

    @property
    def start_time(self) -> Optional[str]:
        value = self._raw.get("start-time")
        return str(value).strip() if value else None

    @property
    def end_time(self) -> Optional[str]:
        value = self._raw.get("end-time")
        return str(value).strip() if value else None

    @property
    def max_workers(self) -> int:
        return max(1, int(self._raw.get("max_workers", 5)))

    @property
    def detail_workers(self) -> int:
        return max(1, int(self._raw.get("detail_workers", 4)))

    @property
    def max_concurrent_processes(self) -> int:
        return max(1, int(self._raw.get("max_concurrent_processes", 3)))

    @property
    def contents_root(self) -> Path:
        value = self._raw.get("contents_root")
        return Path(value) if value else DEFAULT_CONTENTS_ROOT

    @property
    def proxy_api_path(self) -> Path:
        value = self._raw.get("proxy_api_path")
        return Path(value) if value else DEFAULT_PROXY_API_PATH

    def get_run_indices(self) -> list[int]:
        if self.specified:
            return self.specified
        if self.turn:
            start, end = self.turn
            if start > end:
                raise ValueError("turn start cannot be greater than end")
            return list(range(start, end))
        return [0]

    def parse_time_range(self) -> TimeRange:
        """Keep old behavior for total/date/week/month time filtering."""
        st, et = self.start_time, self.end_time
        post_type = self.post_type

        if not st and not et:
            return TimeRange(start_ts="0", end_ts="0", recent_day="0")

        if bool(st) != bool(et):
            raise ValueError("start-time and end-time must both be provided or both empty")

        if post_type != "total":
            raise ValueError("start-time/end-time can only be used when type is total")

        st_dt = datetime.strptime(f"{st} 00:00:00", "%Y-%m-%d %H:%M:%S")
        et_dt = datetime.strptime(f"{et} 23:59:59", "%Y-%m-%d %H:%M:%S")

        if max(st_dt, et_dt) > datetime.now():
            raise ValueError("start-time/end-time cannot be in the future")
        if st_dt > et_dt:
            raise ValueError("start-time cannot be later than end-time")
        if (et_dt - st_dt).days > 30:
            raise ValueError("time span cannot exceed 30 days")

        return TimeRange(
            start_ts=str(round(st_dt.timestamp() * 1000)),
            end_ts=str(round(et_dt.timestamp() * 1000)),
            recent_day="-1",
        )


def create_output_folder(tag: str, contents_root: Path) -> Path:
    tag_dir = contents_root / f"tag-{tag}"
    tag_dir.mkdir(parents=True, exist_ok=True)

    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = tag_dir / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
