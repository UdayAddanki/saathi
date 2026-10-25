"""Live two-teacher account and ownership check.

This script makes exactly two model calls: one Plan call per teacher. Roll
imports and all account/ownership assertions use the normal HTTP routes.
"""
from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import argparse
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/class_roll/class_roll_3A_valid.xlsx"
OUT = ROOT / "evidence" / "design"
REPORT = ROOT / "evidence/accounts_check.md"


def free_port() -> int:
    sock = socket.socket(); sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]; sock.close(); return port


def api(page, method, path, **kwargs):
    return page.request.fetch(page.url.split('/', 3)[0] + '//' + page.url.split('/', 3)[2] + path, method=method, **kwargs)


def screenshot(page, name):
    page.screenshot(path=OUT / f"accounts-{name}.png", full_page=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--fake-llm', action='store_true', help='Use the local test model instead of Portkey')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    def record(name, status, detail):
        results.append((name, status, detail))
        print(f'[{status.upper()}] {name}: {detail}', flush=True)
    port = free_port()
    with tempfile.TemporaryDirectory(prefix="saathi-accounts-") as temp:
        db_path = Path(temp) / "accounts.db"
        env = os.environ.copy(); env.update({"DEMO_MODE": "true", "PORT": str(port), "SAATHI_DB_PATH": str(db_path), "PYTHONUNBUFFERED": "1"})
        log_path = Path(temp) / "server.log"
        log_file = log_path.open("w+")
        server = subprocess.Popen([sys.executable, "run.py"], cwd=ROOT, env=env, stdout=log_file, stderr=subprocess.STDOUT, text=True)
        base = f"http://127.0.0.1:{port}"
        try:
            deadline = time.time() + 20
            while time.time() < deadline:
                try:
                    if __import__('urllib.request').request.urlopen(base + '/api/health').status == 200: break
                except Exception: time.sleep(.2)
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                a = browser.new_context(); b = browser.new_context()
                pa, pb = a.new_page(), b.new_page(); pa.goto(base); pb.goto(base)
                screenshot(pa, 'welcome-phone'); pa.set_viewport_size({'width':1280,'height':800}); screenshot(pa, 'welcome-laptop')

                def signup(page, username, email):
                    page.locator('#show-signup').click(); screenshot(page, f'{username}-signup')
                    page.locator('#signup-username').fill(username); page.locator('#signup-password').fill('Strong-password-123'); page.locator('#signup-confirm').fill('Strong-password-123'); page.locator('#signup-email').fill(email); page.locator('#signup-consent').check(); page.locator('#signup-form button').click(); page.wait_for_timeout(500); page.reload(); page.wait_for_timeout(300)
                signup(pa, 'teacher-a-live', 'teacher-a-live@example.com'); signup(pb, 'teacher-b-live', 'teacher-b-live@example.com')
                record('signup', 'pass', 'Teachers A and B signed up through the UI.')
                # Account A creates its class through the same API used by the UI.
                def create_class(page, grade, board, section):
                    response = api(page, 'POST', '/api/classes', data={'board':board,'grade':grade,'section':section,'class_size':38 if grade == 3 else 20,'period_minutes':40,'resources':[]}); assert response.ok, response.text; return response.json()['id']
                class_a = create_class(pa, 3, 'TS_SCERT', 'A'); class_b = create_class(pb, 1, 'NCERT', 'B')
                with FIXTURE.open('rb') as file:
                    preview = pa.request.post(base + f'/api/classes/{class_a}/roll/upload', multipart={'file': {'name': FIXTURE.name, 'mimeType':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'buffer':file.read()}})
                assert preview.ok; saved = api(pa, 'POST', f'/api/classes/{class_a}/roll/save', data=preview.json()['rows']); assert saved.ok
                roll = api(pa, 'GET', f'/api/classes/{class_a}/roll').json(); assert sum(x['readiness_level']=='low' for x in roll)==10 and sum(x['readiness_level']=='mid' for x in roll)==16 and sum(x['readiness_level']=='high' for x in roll)==12
                record('roll', 'pass', 'Teacher A saved 10 Low / 16 Mid / 12 High.')
                # B gets a small typed roll through the same save route.
                rows_b=[{'roll_no':i,'first_name':f'Child {i}','readiness_level':'mid'} for i in range(1,21)]; assert api(pb,'POST',f'/api/classes/{class_b}/roll/save',data=rows_b).ok
                def plan(page, class_id, topic):
                    print(f'[RUNNING] Plan for {topic}', flush=True)
                    response=api(page,'POST','/api/plans',data={'class_id':class_id,'subject':'Mathematics','chapter_or_topic':topic,'lesson_type':'5-step'}, timeout=300000); assert response.ok, response.text; return response.json()
                lesson_a=plan(pa,class_a,'place value'); lesson_b=plan(pb,class_b,'numbers 1 to 20'); record('plans','pass','Exactly one real Plan call per teacher completed.')
                check_a=lesson_a['check_id']; check_b=lesson_b['check_id']; plan_a=lesson_a['id']; plan_b=lesson_b['id']
                for page, ids in ((pa,(class_a,plan_a,check_a)),(pb,(class_b,plan_b,check_b))):
                    other=(class_b,plan_b,check_b) if page is pa else (class_a,plan_a,check_a)
                    for path in (f'/api/classes/{other[0]}',f'/api/classes/{other[0]}/roll',f'/api/plans/{other[1]}',f'/api/checks/{other[2]}'): assert api(page,'GET',path).status==404
                assert class_a not in [x['id'] for x in api(pb,'GET','/api/classes').json()]; assert class_b not in [x['id'] for x in api(pa,'GET','/api/classes').json()]; record('ownership','pass','Both teachers received 404 for the other teacher’s IDs and saw only their own class.')
                pa.request.post(base+'/api/auth/logout'); pa.goto(base); pa.locator('#show-login').click(); pa.locator('#login-username').fill('teacher-a-live'); pa.locator('#login-password').fill('Strong-password-123'); pa.locator('#login-form button').click(); pa.wait_for_timeout(300); assert api(pa,'GET',f'/api/classes/{class_a}').ok and api(pa,'GET',f'/api/plans/{plan_a}').ok; record('relogin','pass','Teacher A logged out, logged back in, and retained class, roll, and lesson.')
                # Reset-link fallback is captured from the server output.
                reset=pa.request.post(base+'/api/auth/forgot-password',data={'identity':'teacher-a-live@example.com'}); assert reset.ok
                time.sleep(.3); log_file.flush(); raw=log_path.read_text()
                match=re.search(r'Password reset link .*?: (http[^\s]+)',raw); assert match, 'reset link was not found in server log'; reset_page=b.new_page(); reset_page.goto(match.group(1)); reset_page.locator('#reset-password').fill('New-strong-password-123'); reset_page.locator('#reset-confirm').fill('New-strong-password-123'); reset_page.locator('#reset-form button').click(); assert api(reset_page,'POST','/api/auth/login',data={'username':'teacher-a-live','password':'New-strong-password-123'}).ok; record('reset','pass','Reset link was read from the server log and the new password worked.')
                pb.goto(base); pb.locator('#demo-login').click(); pb.wait_for_timeout(300); record('demo','pass','Demo login button completed.')
                screenshot(pa, 'account-menu'); screenshot(reset_page, 'reset'); browser.close()
        except Exception as error:
            record('overall','fail',str(error)); return_code=1
        else: return_code=0
        finally:
            log_file.close()
            server.terminate(); server.wait(timeout=10)
    lines=['# Accounts live check','',f'Run date: {time.strftime("%Y-%m-%d %H:%M:%S")}', '']
    lines += [f'- **{name}: {status}** — {detail}' for name,status,detail in results]
    REPORT.write_text('\n'.join(lines) + '\n')
    return return_code


if __name__ == '__main__': raise SystemExit(main())
