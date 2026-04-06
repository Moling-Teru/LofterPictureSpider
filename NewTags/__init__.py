# -*- coding: utf-8 -*-
"""NewTags package exports."""

from .api import LofterAPI
from .config import Config
from .crawler import run_crawler
from .downloader import Downloader
from .parser import PostType
from .proxy import ProxyPool

__all__ = [
    "Config",
    "LofterAPI",
    "ProxyPool",
    "Downloader",
    "PostType",
    "run_crawler",
]
