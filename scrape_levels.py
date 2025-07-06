#!/usr/bin/env python3
"""
Download Queens puzzle data: HTML, screenshot, JSON, and index SSV file for each level.
Interactive options:
 1) Download all levels
 2) Download specific levels
 3) Download missing levels (based on existing index.ssv)
At the end, report successes and failures with reasons.
Logs saved to 'logs/levels_download.log'.
"""
from pathlib import Path
import re
import json
import csv
import logging
from typing import List, Optional, Tuple
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup

# Configure logging
def setup_logging():
    logs_dir = Path('logs')
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / 'levels_download.log'
    handlers = [
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers
    )


def html_to_json(html: str) -> List[dict]:
    """
    Parse HTML of the puzzle grid and extract each square's
    row, column, background color, and any thick-border classes.
    """
    soup = BeautifulSoup(html, 'html.parser')
    data = []
    for div in soup.select('div.square'):
        row = int(div.get('data-row', -1))
        col = int(div.get('data-col', -1))
        style = div.get('style', '')
        m = re.search(r"background-color\s*:\s*([^;]+)", style)
        color = m.group(1).strip() if m else ''
        classes = div.get('class', []) or []
        borders = [cls for cls in classes if 'thick-border' in cls]
        data.append({'row': row, 'col': col, 'color': color, 'borders': borders})
    return data


def fetch_levels(page: Page, link: str) -> Optional[List[int]]:
    """
    Navigate to the homepage and extract available level numbers.
    Returns a sorted list of level IDs.
    """
    logging.info(f"Fetching levels from {link}")
    page.goto(link, wait_until='networkidle')
    anchors = page.query_selector_all('a[href^="/level/"]')
    levels = []
    for a in anchors:
        href = a.get_attribute('href') or ''
        m = re.search(r"/level/(\d+)", href)
        if m:
            levels.append(int(m.group(1)))
    levels = sorted(set(levels))
    if not levels:
        logging.error("No level links found on the homepage.")
        return None
    logging.info(f"Found levels: {levels}")
    return levels


def download_puzzle(page: Page, link: str, levels: List[int], base_dir: Path) -> None:
    """
    For each level, save HTML, screenshot, JSON, update index SSV file,
    and report success/failure counts with reasons.
    """
    html_dir = base_dir / "html"
    img_dir = base_dir / "pictures"
    json_dir = base_dir / "json"
    for d in (html_dir, img_dir, json_dir):
        d.mkdir(parents=True, exist_ok=True)

    selector = "div.board__grid"
    fallback = 'div[style*="grid-template-columns"]'
    successes: List[int] = []
    failures: List[Tuple[int, str]] = []
    index_rows: List[Tuple[int, str, str, str]] = []

    for lvl in levels:
        try:
            logging.info(f"Processing level {lvl}")
            page.goto(f"{link}level/{lvl}", wait_until='networkidle')

            grid_el = page.query_selector(selector) or page.query_selector(fallback)
            if not grid_el:
                reason = "Puzzle container not found"
                logging.warning(f"Level {lvl} failed: {reason}")
                failures.append((lvl, reason))
                continue

            # Save HTML
            html_content = grid_el.inner_html()
            html_file = html_dir / f"puzzle{lvl}.html"
            html_file.write_text(html_content, encoding='utf-8')

            # Save image
            img_file = img_dir / f"puzzle{lvl}.png"
            grid_el.screenshot(path=str(img_file))

            # Save JSON
            data = html_to_json(html_content)
            json_file = json_dir / f"puzzle{lvl}.json"
            json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

            # Determine grid size
            if data:
                max_row = max(item['row'] for item in data)
                max_col = max(item['col'] for item in data)
                size_str = f"{max_row+1} by {max_col+1}"
            else:
                size_str = ''

            index_rows.append((lvl, str(img_file), str(json_file), size_str))
            successes.append(lvl)
            logging.info(f"Level {lvl} downloaded successfully")

        except Exception as e:
            reason = str(e)
            logging.error(f"Level {lvl} failed: {reason}", exc_info=True)
            failures.append((lvl, reason))

    # Write index SSV
    if index_rows:
        ssv_file = base_dir / "index.ssv"
        with ssv_file.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["level","image_path","json_path","grid_size"])
            writer.writerows(index_rows)
        logging.info(f"Saved index SSV: {ssv_file}")

    # Print report
    print("\nDownload Report:")
    print(f"  Successful levels: {len(successes)}")
    print(f"  Failed levels: {len(failures)}")
    if failures:
        print("  Failure details:")
        for lvl, reason in failures:
            print(f"   - Level {lvl}: {reason}")


def get_user_choice() -> str:
    """Prompt user to select operation."""
    while True:
        print("Options:")
        print("1) Download all levels")
        print("2) Download specific levels")
        print("3) Download missing levels")
        choice = input("Enter choice (1/2/3): ").strip()
        if choice in ("1","2","3"):
            return choice
        print("Invalid choice. Please enter 1, 2, or 3.")


def get_specific_levels(available: List[int]) -> List[int]:
    """Prompt for comma-separated levels and validate."""
    max_lvl = max(available)
    while True:
        raw = input(f"Enter levels as comma-separated list (1-{max_lvl}): ").strip()
        parts = [p.strip() for p in raw.split(',') if p.strip()]
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            print("Entries must be integers. Try again.")
            continue
        invalid = [n for n in nums if n not in available]
        if invalid:
            print(f"Levels not available: {invalid}. Available: {available}")
            continue
        return sorted(set(nums))


def read_missing_levels(base_dir: Path, available: List[int]) -> List[int]:
    """Read index.ssv and compute missing levels."""
    ssv = base_dir / "index.ssv"
    if not ssv.exists():
        print("index.ssv not found. Generate index first.")
        return []
    existing = []
    with ssv.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            existing.append(int(row['level']))
    missing = [lvl for lvl in available if lvl not in existing]
    print(f"Missing levels: {missing}")
    return missing


def main():
    setup_logging()
    link = "https://queensgame.vercel.app/"
    base_dir = Path('levels')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        available = fetch_levels(page, link) or []
        if not available:
            logging.error("No levels found. Exiting.")
            return

        choice = get_user_choice()
        if choice == "1":
            to_download = available
        elif choice == "2":
            to_download = get_specific_levels(available)
        else:
            to_download = read_missing_levels(base_dir, available)
            if not to_download:
                print("No missing levels to download. Exiting.")
                return

        logging.info(f"Levels to download: {to_download}")
        download_puzzle(page, link, to_download, base_dir)
        browser.close()


if __name__ == "__main__":
    main()
