# -*- coding: utf-8 -*-
"""Single-run crawler pipeline.

This module keeps the original behavior:
- Fetch a tag page by offset
- Parse post IDs/types
- Resolve content details
- Download with ThreadPoolExecutor (multi-threading)
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from .api import LofterAPI
    from .color import color
    from .config import Config, create_output_folder
    from .downloader import AsyncLineLogger, Downloader
    from .parser import (
        PostType,
        extract_posts,
        get_likes,
        parse_image_items,
        parse_image_links,
        parse_is_paid,
        parse_text_content,
        parse_title,
    )
    from .proxy import ProxyPool
except ImportError:
    from api import LofterAPI
    from color import color
    from config import Config, create_output_folder
    from downloader import AsyncLineLogger, Downloader
    from parser import (
        PostType,
        extract_posts,
        get_likes,
        parse_image_items,
        parse_image_links,
        parse_is_paid,
        parse_text_content,
        parse_title,
    )
    from proxy import ProxyPool


@dataclass(frozen=True)
class DownloadTask:
    content_type: int
    payload: str
    post_id: int
    blog_name: str
    title: str
    is_paid: int


def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _resolve_single_post(
    api: LofterAPI,
    post_info: tuple[list, int],
    proxy: Optional[dict[str, str]],
) -> tuple[list[DownloadTask], int, int]:
    """Resolve text/image post to concrete downloadable tasks.

    Returns:
        tasks, invalid_post_count, invalid_link_count
    """
    post_data, post_type = post_info
    post_id = post_data[0]
    blog_name = post_data[1]

    detail = api.get_post_detail(post_id, blog_name, proxy=proxy)
    if not detail:
        return [], 1, 0

    title = parse_title(detail)
    is_paid = parse_is_paid(detail)

    if post_type == PostType.TEXT:
        content = parse_text_content(detail)
        if not content:
            return [], 1, 0
        return [DownloadTask(PostType.TEXT, content, post_id, blog_name, title, is_paid)], 0, 0

    if post_type == PostType.IMAGE:
        image_links = parse_image_links(detail)
        if not image_links:
            return [], 1, 0

        items, invalid_link_count = parse_image_items(
            image_links=image_links,
            post_id=post_id,
            blog_name=blog_name,
            title=title,
            is_paid=is_paid,
        )

        tasks = [
            DownloadTask(
                content_type=PostType.IMAGE,
                payload=item[0],
                post_id=item[1],
                blog_name=item[2],
                title=item[3],
                is_paid=item[4],
            )
            for item in items
        ]
        invalid_post_count = 1 if not tasks else 0
        return tasks, invalid_post_count, invalid_link_count

    return [], 1, 0


def _build_download_path(base_path: Path, run_index: int, seq: int, content_type: int) -> Path:
    stem = f"{run_index}-{seq}"
    if content_type == PostType.TEXT:
        return base_path / f"{stem}.html"
    if content_type == PostType.VIDEO:
        return base_path / f"{stem}.mp4"
    return base_path / f"{stem}.png"


def run_crawler(run_index: int, output_path: Path, use_proxy: bool) -> None:
    cfg = Config()
    if not cfg.tag:
        raise ValueError("tag is empty in config.yaml")

    print(color.blue(f"Start run {run_index + 1}: {get_timestamp()}"))

    time_range = cfg.parse_time_range()
    api = LofterAPI(timeout=30)
    proxy_pool = ProxyPool(cfg.proxy_api_path)

    list_proxy = proxy_pool.get_proxies(1, use_proxy=use_proxy)[0]
    response = api.request_tag_posts(
        tag=cfg.tag,
        offset=10 * run_index,
        post_type=cfg.post_type,
        post_ymd_st=time_range.start_ts,
        post_ymd_et=time_range.end_ts,
        recent_day=time_range.recent_day,
        proxy=list_proxy,
    )

    if not response:
        print(color.red("No response for tagPosts request"))
        return

    posts = list(extract_posts(response))
    likes_info = get_likes(response)
    likes, likes_low = likes_info if likes_info else (None, None)

    target_likes = cfg.likes
    if target_likes is not None and likes is not None and likes < target_likes:
        print(color.yellow(f"likes({likes}) < target({target_likes}), skip run"))
        return

    print(f"{get_timestamp()} Parsed {len(posts)} posts")

    detail_candidates = [p for p in posts if p[1] in (PostType.TEXT, PostType.IMAGE)]
    video_posts = [p for p in posts if p[1] == PostType.VIDEO]

    download_tasks: list[DownloadTask] = []
    invalid_post_count = 0
    invalid_link_count = 0

    for post_data, _ in video_posts:
        if not post_data or not post_data[0]:
            invalid_post_count += 1
            continue
        download_tasks.append(
            DownloadTask(
                content_type=PostType.VIDEO,
                payload=post_data[0],
                post_id=post_data[1],
                blog_name=post_data[2],
                title=post_data[3],
                is_paid=post_data[4],
            )
        )

    # Fetch post details in a small pool for better API throughput.
    if detail_candidates:
        detail_proxies = proxy_pool.get_proxies(max(1, cfg.detail_workers), use_proxy=use_proxy)
        with ThreadPoolExecutor(max_workers=cfg.detail_workers) as detail_executor:
            future_map = {}
            for idx, post_info in enumerate(detail_candidates):
                proxy = detail_proxies[idx % len(detail_proxies)]
                future = detail_executor.submit(_resolve_single_post, api, post_info, proxy)
                future_map[future] = post_info

            for future in as_completed(future_map):
                tasks, invalid_posts, invalid_links = future.result()
                invalid_post_count += invalid_posts
                invalid_link_count += invalid_links
                download_tasks.extend(tasks)

    print(
        f"{get_timestamp()} Resolved download tasks: {len(download_tasks)} "
        f"(invalid_posts={invalid_post_count}, invalid_links={invalid_link_count})"
    )

    if not download_tasks:
        print(color.yellow("No downloadable content"))
        return

    downloader = Downloader(timeout=30)
    log_writer = AsyncLineLogger(output_path / f"download_log_{run_index}.txt")
    error_writer = AsyncLineLogger(output_path / "errors.txt")

    success_count = 0
    failure_count = 0
    proxies = proxy_pool.get_proxies(max(1, cfg.max_workers), use_proxy=use_proxy)

    def _download_one(seq: int, task: DownloadTask, proxy: Optional[dict[str, str]]) -> bool:
        file_path = _build_download_path(output_path, run_index, seq, task.content_type)
        try:
            if task.content_type == PostType.IMAGE:
                downloader.download_image(task.payload, file_path, proxy=proxy)
            elif task.content_type == PostType.TEXT:
                downloader.save_text_html(task.payload, file_path, title=task.title)
            elif task.content_type == PostType.VIDEO:
                downloader.download_video(task.payload, file_path, proxy=proxy)
            else:
                raise ValueError(f"unknown content type: {task.content_type}")

            log_writer.write_line(
                f"Title: {task.title}, ID: {task.post_id}, Blog: {task.blog_name}, "
                f"Gift: {task.is_paid}, Path: {file_path}"
            )
            return True
        except Exception as exc:
            error_writer.write_line(f"{task.payload}")
            log_writer.write_line(
                f"---> X Error: Title={task.title}, ID={task.post_id}, Blog={task.blog_name}, "
                f"Gift={task.is_paid}, Cause={exc}"
            )
            return False

    run_label = f"run#{run_index + 1}"

    with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
        futures = {}
        for seq, task in enumerate(download_tasks, start=1):
            proxy = proxies[(seq - 1) % len(proxies)]
            future = executor.submit(_download_one, seq, task, proxy)
            futures[future] = seq

        total = len(futures)
        for future in as_completed(futures):
            seq = futures[future]
            try:
                ok = future.result()
                if ok:
                    success_count += 1
                else:
                    failure_count += 1
                print(f"Progress {run_label}: {success_count + failure_count}/{total} item#{seq}")
            except Exception as exc:
                failure_count += 1
                print(color.red(f"Progress {run_label} error on item#{seq}: {exc}"))

    log_writer.write_line(f"Summary: success={success_count}, failed={failure_count}")
    log_writer.write_line(f"Summary: likes_high={likes}, likes_low={likes_low}")
    log_writer.write_line(
        f"Summary: invalid_posts={invalid_post_count}, invalid_links={invalid_link_count}"
    )

    log_writer.close()
    error_writer.close()

    print(color.green(f"Run {run_index + 1} done at {get_timestamp()}"))


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="NewTags crawler (single run)")
    parser.add_argument("--offset", default=0, type=int)
    parser.add_argument("--path", default="", type=str)
    parser.add_argument("--proxies", default="0", type=str)

    args = parser.parse_args(argv)

    cfg = Config()
    output_path = Path(args.path) if args.path else create_output_folder(cfg.tag, cfg.contents_root)
    output_path.mkdir(parents=True, exist_ok=True)

    use_proxy = bool(int(args.proxies))

    start = time.time()
    print(f"{get_timestamp()} Program start")
    print(color.cyan("=" * 80))

    run_crawler(args.offset, output_path, use_proxy)

    elapsed = time.time() - start
    print(color.yellow(f"Total elapsed: {elapsed:.2f}s"))


if __name__ == "__main__":
    main()
