# NewTags

Refactored LOFTER tag crawler.

## Goals

- Keep multi-threaded behavior.
- Keep compatibility with old CLI args and config fields.
- Improve code readability and reduce duplicated logic.
- Improve performance via session pooling and cached proxy rotation.

## Structure

- run.py: entry script
- launcher.py: task-level concurrent launcher
- crawler.py: single-run crawler pipeline
- api.py: LOFTER API client with retry + connection pool
- proxy.py: thread-safe proxy pool with cache
- parser.py: response parsing and content extraction
- downloader.py: image/text/video downloader with async log writer
- config.py: typed config and path utilities

## Usage

Launcher mode (default):

python NewTags/run.py

Single-run mode:

python NewTags/run.py --single --offset 0 --path NewTags/Contents/tag-demo/2026-03-29_12-00-00 --proxies 0

## Compatibility Notes

- Compatible CLI args for single run:
  - --offset
  - --path
  - --proxies
- Compatible config fields:
  - tag, type, turn, specified, likes, start-time, end-time
- Added optional fields:
  - max_workers, max_concurrent_processes, detail_workers, contents_root, proxy_api_path

## Output

- Downloaded content under NewTags/Contents/tag-{tag}/{timestamp}
- Per-run log: download_log_{offset}.txt
- Error list: errors.txt
