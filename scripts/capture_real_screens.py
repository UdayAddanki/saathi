"""Capture real screens for the report and slides by running one loop as the demo teacher.

The loop runs in the browser exactly as a teacher would use it, against a
temporary database (demo account + committed fixtures, no real classroom
data). It makes real model calls: one lesson plan, five sheet readings, one
Next steps run and one worksheet run (about 2 US cents).

    python3 scripts/capture_real_screens.py

Screens are saved to evidence/design/real-*.png.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence' / 'design'
PORT = 8011
BASE = f'http://localhost:{PORT}'


def wait_for_server() -> None:
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + '/api/health')
            return
        except Exception:
            time.sleep(0.5)
    raise SystemExit('The app did not start.')


def save(page, name: str, selector: str | None = None, max_height: int | None = None) -> None:
    """Screenshot the page or one element, optionally keeping only its top part."""
    path = OUT / f'real-{name}.png'
    if selector:
        element = page.locator(selector).first
        element.scroll_into_view_if_needed()
        # Clip in page coordinates (not viewport coordinates), so elements far down the page crop correctly.
        rect = element.evaluate('el => { const r = el.getBoundingClientRect(); return {x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: r.height}; }')
        page.evaluate('document.querySelector(".tabs") && (document.querySelector(".tabs").style.visibility = "hidden")')
        clip = {'x': rect['x'], 'y': rect['y'], 'width': rect['width'], 'height': min(rect['height'], max_height or rect['height'])}
        page.screenshot(path=str(path), clip=clip, full_page=True)
        page.evaluate('document.querySelector(".tabs") && (document.querySelector(".tabs").style.visibility = "")')
    else:
        page.screenshot(path=str(path))
    print('saved', path.name, flush=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    db = Path(tempfile.mkdtemp(prefix='saathi-screens-')) / 'screens.db'
    env = dict(os.environ, SAATHI_DB_PATH=str(db), DEMO_MODE='true', PORT=str(PORT), PYDANTIC_AI_NO_BANNER='1')
    server = subprocess.Popen([sys.executable, 'run.py'], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for_server()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.goto(BASE)
            page.click('#demo-login')
            page.wait_for_selector('#class-select option', state='attached')
            page.wait_for_timeout(800)

            # Check ①: the class roll grouped by readiness level.
            page.click('[data-view="check-view"]')
            page.wait_for_timeout(1500)
            page.set_input_files('#check-view .card input[type=file]', str(ROOT / 'tests/fixtures/class_roll/class_roll_3A_valid.xlsx'))
            page.click('#check-view .card button.primary')
            page.wait_for_function("document.querySelector('#check-view .card').innerText.includes('Bhavya')", timeout=30000)
            page.wait_for_timeout(1000)
            save(page, 'roll', '#check-view .card', max_height=700)

            # Plan: classroom context, topic, lesson type, then a real plan.
            page.click('[data-view="plan-view"]')
            page.fill('#current-situation', 'Mixed levels: most children read 2-digit numbers; about a third confuse tens and ones.')
            page.fill('#unit-goal', 'Children read, write and compare 3-digit numbers using place value.')
            page.select_option('#subject-select', 'Mathematics')
            page.fill('#chapter-input', 'Numbers up to 999')
            page.fill('#topic-input', 'Place value of 3-digit numbers')
            save(page, 'plan-form', '#plan-form', max_height=820)
            page.click('#prepare-button')
            page.wait_for_function("document.querySelector('#plan-result').innerText.length > 400", timeout=180000)
            page.wait_for_timeout(1500)
            save(page, 'plan-vision', '#plan-result', max_height=640)
            page.evaluate("document.querySelectorAll('#plan-result details').forEach((d) => d.open = true)")
            page.wait_for_timeout(500)
            save(page, 'plan-method', '#plan-result details:nth-of-type(2)', max_height=640)

            # Check ②–④: choose the lesson, upload the five sample sheets, see the analysis.
            page.click('[data-view="check-view"]')
            page.wait_for_selector('#lesson-select option', state='attached', timeout=30000)
            page.wait_for_timeout(1500)
            page.click('.submission-card')
            page.wait_for_timeout(500)
            page.eval_on_selector('.submission-upload input[type=file]', 'el => el.multiple = true')
            sheets = sorted(str(path) for path in (ROOT / 'tests/fixtures/submissions/grade3').glob('roll_*.png'))
            page.set_input_files('.submission-upload input[type=file]', sheets)
            page.wait_for_function("document.body.innerText.includes('Answer sheets read') || document.body.innerText.includes('could not')", timeout=240000)
            page.wait_for_timeout(2000)
            save(page, 'analysis', '#check-step-analysis')

            # Next steps and a worksheet.
            page.click('[data-view="next-view"]')
            page.wait_for_timeout(1500)
            page.select_option('#next-check-select', index=0)
            page.dispatch_event('#next-check-select', 'change')
            page.wait_for_function("document.querySelector('#next-content').innerText.length > 300", timeout=180000)
            page.wait_for_timeout(1500)
            save(page, 'next-steps', '#next-content', max_height=700)
            page.click('#resources-tab-button')
            page.click('#generate-worksheets')
            page.wait_for_function("document.querySelector('#resource-content').innerText.length > 200", timeout=180000)
            page.wait_for_timeout(1500)
            save(page, 'worksheet', '#resources-tab-content', max_height=700)
            browser.close()
    finally:
        server.terminate()
        server.wait()


if __name__ == '__main__':
    main()
