# -*- coding: utf-8 -*-
"""Parsing helpers for tag list and post details."""

from __future__ import annotations

import json
from typing import Any, Iterator, Optional


class PostType:
    TEXT = 0
    IMAGE = 1
    VIDEO = 2


def extract_posts(data: dict[str, Any]) -> Iterator[tuple[list[Any], int]]:
    """
    Yield posts from tag list response.

    Output compatibility:
    - text/image => ([post_id, blog_name], type)
    - video => ([video_url, post_id, blog_name, title, show_gift], 2)
    """
    posts = data.get("data", {}).get("list", []) if isinstance(data, dict) else []
    for item in posts:
        post_view = item.get("postData", {}).get("postView", {})
        blog_name = item.get("blogInfo", {}).get("blogName", "")
        post_id = post_view.get("id")
        photo_count = post_view.get("photoCount", 0)

        if photo_count == 0:
            video_view = post_view.get("videoPostView")
            if video_view:
                video_url = video_view.get("videoInfo", {}).get("originUrl")
                title = post_view.get("title", "")
                show_gift = post_view.get("showGift", 0)
                yield [video_url, post_id, blog_name, title, show_gift], PostType.VIDEO
            else:
                yield [post_id, blog_name], PostType.TEXT
        else:
            yield [post_id, blog_name], PostType.IMAGE


def get_likes(data: dict[str, Any]) -> Optional[tuple[int, int]]:
    posts = data.get("data", {}).get("list", []) if isinstance(data, dict) else []
    if not posts:
        return None
    high = posts[0].get("postData", {}).get("postCount", {}).get("favoriteCount")
    low = posts[-1].get("postData", {}).get("postCount", {}).get("favoriteCount")
    if high is None or low is None:
        return None
    return int(high), int(low)


def parse_title(content: dict[str, Any]) -> str:
    return (
        content.get("response", {})
        .get("posts", [{}])[0]
        .get("post", {})
        .get("title", "")
    )


def parse_is_paid(content: dict[str, Any]) -> int:
    return int(
        content.get("response", {})
        .get("posts", [{}])[0]
        .get("post", {})
        .get("showGift", 0)
    )


def parse_text_content(content: dict[str, Any]) -> Optional[str]:
    text = (
        content.get("response", {})
        .get("posts", [{}])[0]
        .get("post", {})
        .get("content")
    )
    if not isinstance(text, str):
        return None
    return text.strip().replace("\n", "")


def parse_image_links(content: dict[str, Any]) -> Optional[str]:
    links = (
        content.get("response", {})
        .get("posts", [{}])[0]
        .get("post", {})
        .get("photoLinks")
    )
    if not isinstance(links, str):
        return None
    return links


def parse_image_items(
    image_links: str,
    post_id: int,
    blog_name: str,
    title: str,
    is_paid: int,
) -> tuple[list[list[Any]], int]:
    items: list[list[Any]] = []
    error_count = 0

    try:
        payload = json.loads(image_links)
    except json.JSONDecodeError:
        return items, 1

    if not isinstance(payload, list):
        return items, 1

    for entry in payload:
        raw_url = entry.get("raw") if isinstance(entry, dict) else None
        if not raw_url:
            error_count += 1
            continue
        items.append([raw_url, post_id, blog_name, title, is_paid])

    return items, error_count


def parse_video_url(content: dict[str, Any]) -> Optional[str]:
    embed = (
        content.get("response", {})
        .get("posts", [{}])[0]
        .get("post", {})
        .get("embed")
    )
    if not isinstance(embed, str):
        return None
    try:
        payload = json.loads(embed)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    url = payload.get("originUrl")
    return str(url) if url else None
