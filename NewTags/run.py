# -*- coding: utf-8 -*-
"""Entry script.

Behavior:
- no args: run launcher mode
- with --single: run single crawler mode (used by launcher)
"""

from __future__ import annotations

import sys

import crawler
import launcher


def main() -> None:
    argv = sys.argv[1:]

    if "--single" in argv:
        filtered = [arg for arg in argv if arg != "--single"]
        crawler.main(filtered)
        return

    launcher.main(argv)


if __name__ == "__main__":
    main()
