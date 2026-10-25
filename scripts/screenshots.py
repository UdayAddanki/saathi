"""Capture the visual-design evidence set with a local isolated app.

The script starts Saathi with DEMO_MODE and a temporary SQLite database. It
captures the public screens at phone and laptop sizes, reduced motion, and
print media. If PORTKEY_API_KEY is available, the lesson/upload preparation
hooks can be enabled for the permitted demo calls; the screenshots themselves
never call the model in a loop.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "design"


def capture(page, name: str, width: int, height: int, reduced: bool = False, media: str | None = None):
    page.set_viewport_size({"width": width, "height": height})
    if media:
        page.emulate_media(media=media)
    page.screenshot(path=OUT / f"{name}-{width}x{height}.png", full_page=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="saathi-screenshot-") as db_dir:
        env = os.environ.copy()
        env.update({"DEMO_MODE": "true", "PORT": "8765", "SAATHI_DB_PATH": str(Path(db_dir) / "saathi.db")})
        server = subprocess.Popen([sys.executable, "run.py"], cwd=ROOT, env=env)
        try:
            time.sleep(2)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto("http://127.0.0.1:8765", wait_until="networkidle")
                for width, height, label in ((390, 844, "phone"), (1280, 800, "laptop")):
                    capture(page, f"plan-form-{label}", width, height)
                    page.locator('[data-view="check-view"]').click()
                    page.wait_for_timeout(300)
                    capture(page, f"check-{label}", width, height)
                    page.locator('[data-view="next-view"]').click()
                    page.wait_for_timeout(300)
                    capture(page, f"next-steps-{label}", width, height)
                    page.locator("#resources-tab-button").click()
                    capture(page, f"additional-resources-{label}", width, height)
                page.emulate_media(reduced_motion="reduce")
                capture(page, "reduced-motion", 390, 844, reduced=True)
                page.emulate_media(media="print")
                capture(page, "lesson-plan-print", 1280, 800, media="print")
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    main()
