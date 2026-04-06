# -*- coding: utf-8 -*-
"""Multi-task launcher.

Keeps original semantics:
- Launcher runs multiple offsets concurrently (task-level parallelism)
- Each offset is executed by crawler.py which still uses thread pool downloads
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

try:
    from .color import color
    from .config import CONFIG_PATH, Config, create_output_folder
except ImportError:
    from color import color
    from config import CONFIG_PATH, Config, create_output_folder


def _run_one_task(
    semaphore: threading.Semaphore,
    run_index: int,
    run_order: int,
    output_path: Path,
    use_proxy: bool,
) -> None:
    with semaphore:
        print(
            f"[Launcher] scheduling run #{run_order} "
            f"(offset={run_index}, range={run_index * 10 + 1}-{run_index * 10 + 10})"
        )

        cmd = [
            sys.executable,
            str(Path(__file__).with_name("run.py")),
            "--single",
            "--offset",
            str(run_index),
            "--path",
            str(output_path),
            "--proxies",
            "1" if use_proxy else "0",
        ]

        process = subprocess.Popen(cmd, cwd=str(Path(__file__).resolve().parent))
        process.wait()

        if process.returncode == 0:
            print(f"[Launcher] run #{run_order} done")
        else:
            print(color.red(f"[Launcher] run #{run_order} failed (code={process.returncode})"))


def main_launcher(workers: Optional[int] = None, use_proxy: bool = False) -> None:
    cfg = Config()
    if not cfg.tag:
        raise ValueError("tag is empty in config.yaml")

    run_indices = cfg.get_run_indices()
    max_concurrent = workers or cfg.max_concurrent_processes
    output_path = create_output_folder(cfg.tag, cfg.contents_root)

    shutil.copy(CONFIG_PATH, output_path / "config.yaml")

    print(color.cyan("=" * 60))
    print("NewTags launcher")
    print(f"tasks: {len(run_indices)}")
    print(f"max concurrent tasks: {max_concurrent}")
    print(f"use proxy: {use_proxy}")
    print(f"output: {output_path}")
    print(color.cyan("=" * 60))

    semaphore = threading.Semaphore(max_concurrent)
    threads: list[threading.Thread] = []

    start = time.time()

    for run_order, run_index in enumerate(run_indices, start=1):
        t = threading.Thread(
            target=_run_one_task,
            args=(semaphore, run_index, run_order, output_path, use_proxy),
            daemon=False,
        )
        threads.append(t)
        t.start()
        time.sleep(0.5)

    for t in threads:
        t.join()

    elapsed = time.time() - start
    print(color.green(f"All tasks finished in {elapsed:.2f}s"))


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="NewTags launcher")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--proxy", action="store_true")
    args = parser.parse_args(argv)

    main_launcher(workers=args.workers, use_proxy=args.proxy)


if __name__ == "__main__":
    main()
