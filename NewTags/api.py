# -*- coding: utf-8 -*-
"""HTTP client wrappers for LOFTER APIs."""

from __future__ import annotations

from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session(max_retries: int = 3, pool_size: int = 16) -> requests.Session:
    retry = Retry(
        total=max_retries,
        backoff_factor=0.25,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=pool_size, pool_maxsize=pool_size)

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class LofterAPI:
    TAG_POSTS_URL = "https://api.lofter.com/newapi/tagPosts.json"
    POST_DETAIL_URL = "https://api.lofter.com/oldapi/post/detail.api"

    TAG_HEADERS = {
        "x-device": "",
        "lofproduct": "lofter-android-8.2.34",
        "user-agent": "LOFTER-Android 8.2.34 (RMX3888; Android 12; null) WIFI",
        "accept-encoding": "gzip",
        "content-type": "application/x-www-form-urlencoded; charset=utf-8",
    }

    DETAIL_HEADERS = {
        "x-device": "",
        "lofproduct": "lofter-android-8.2.23",
        "user-agent": "LOFTER-Android 8.2.23 (RMX3888; Android 9; null) WIFI",
        "accept-encoding": "gzip",
        "content-type": "application/x-www-form-urlencoded",
    }

    TAG_BODY = {
        "product": "lofter-android-8.2.34",
        "postTypes": "",
        "postYm": "",
        "returnGiftCombination": "",
        "recentDay": "0",
        "protectedFlag": "0",
        "range": "0",
        "firstpermalink": "null",
        "style": "0",
    }

    def __init__(self, timeout: int = 30, session: Optional[requests.Session] = None) -> None:
        self.timeout = timeout
        self.session = session or build_session()

    def request_tag_posts(
        self,
        *,
        tag: str,
        offset: int,
        post_type: str,
        post_ymd_st: str,
        post_ymd_et: str,
        recent_day: str,
        proxy: Optional[dict[str, str]] = None,
    ) -> Optional[dict[str, Any]]:
        body = {
            **self.TAG_BODY,
            "tag": tag,
            "type": post_type,
            "offset": str(offset),
            "postYmdSt": post_ymd_st,
            "postYmdEt": post_ymd_et,
            "recentDay": recent_day,
        }
        try:
            response = self.session.post(
                self.TAG_POSTS_URL,
                headers=self.TAG_HEADERS,
                data=body,
                timeout=self.timeout,
                proxies=proxy,
            )
            response.raise_for_status()
            if not response.text.strip():
                return None
            result = response.json()
            if result.get("data", {}).get("offset") == -1:
                return None
            return result
        except Exception:
            return None

    def get_post_detail(
        self,
        post_id: int,
        blog_domain: str,
        proxy: Optional[dict[str, str]] = None,
    ) -> Optional[dict[str, Any]]:
        params = {"product": "lofter-android-8.2.23"}
        body = {
            "supportposttypes": "1,2,3,4,5,6",
            "blogdomain": f"{blog_domain}.lofter.com",
            "offset": "0",
            "requestType": "0",
            "postdigestnew": "1",
            "postid": str(post_id),
            "checkpwd": "1",
            "needgetpoststat": "1",
        }
        try:
            response = self.session.post(
                self.POST_DETAIL_URL,
                headers=self.DETAIL_HEADERS,
                params=params,
                data=body,
                timeout=self.timeout,
                proxies=proxy,
            )
            response.raise_for_status()
            if not response.text.strip():
                return None
            result = response.json()
            if result.get("meta", {}).get("status") != 200:
                return None
            return result
        except Exception:
            return None
