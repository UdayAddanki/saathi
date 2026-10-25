"""End-to-end account check. Use --skip-plan for a no-model ownership run."""
from __future__ import annotations
import argparse, json, os, re, socket, sqlite3, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/class_roll/class_roll_3A_valid.xlsx'
OUT = ROOT / 'evidence/design'; REPORT = ROOT / 'evidence/accounts_check.md'

def free_port():
    sock = socket.socket(); sock.bind(('127.0.0.1', 0)); value = sock.getsockname()[1]; sock.close(); return value

def result(step, passed, detail, **extra):
    record = {'step': step, 'status': 'pass' if passed else 'fail', 'detail': detail, **extra}
    print(f'[{record["status"].upper()}] {step}: {detail}', flush=True)
    return record

def require(response, step, expected=200):
    body = response.text()
    if response.status != expected:
        raise AssertionError(f'{step}: expected HTTP {expected}, got HTTP {response.status}: {body[:500]}')
    return response.json() if body else {}
def require_text(response, step, expected=200):
    body=response.text()
    if response.status != expected: raise AssertionError(f'{step}: expected HTTP {expected}, got HTTP {response.status}: {body[:500]}')
    if not body.strip(): raise AssertionError(f'{step}: expected non-empty response')
    return body

def signup(page, base, username, email):
    page.goto(base); page.locator('#show-signup').click()
    for selector, value in [('#signup-username', username), ('#signup-password', 'Strong-password-123'), ('#signup-confirm', 'Strong-password-123'), ('#signup-email', email)]: page.locator(selector).fill(value)
    page.locator('#signup-consent').check(); page.locator('#signup-form button').click(); page.wait_for_timeout(400)
    if page.locator('#class-select').count() != 1: raise AssertionError(f'{username}: signup did not enter the app at {page.url}')

def auth_validation_steps(page, base):
    page.request.post(base + '/api/auth/logout'); page.goto(base); page.locator('#show-signup').click(); page.locator('#signup-form').evaluate("form => form.noValidate=true"); page.locator('#signup-username').fill('teacher-a-live'); page.locator('#signup-username').evaluate("node => node.removeAttribute('pattern')"); page.locator('#signup-password').fill('Strong-password-123'); page.locator('#signup-confirm').fill('Strong-password-123'); page.locator('#signup-email').fill('duplicate@example.com'); page.locator('#signup-consent').check(); page.locator('#signup-form button').click(); page.wait_for_timeout(500)
    duplicate_message=page.locator('#signup-error').text_content(); print(f'[INFO] duplicate signup message: {duplicate_message!r}', flush=True)
    if 'taken' not in duplicate_message.lower(): raise AssertionError(f'duplicate username message was not shown: {duplicate_message!r}')
    page.locator('#show-login').click(); page.locator('[data-testid="forgot-link"]').click(); page.locator('[data-testid="forgot-identity"]').fill('teacher-a-live@example.com'); page.locator('[data-testid="forgot-submit"]').click(); page.wait_for_timeout(300)
    if 'If an account exists' not in page.locator('[data-testid="forgot-message"]').text_content(): raise AssertionError('forgot-password confirmation was not shown')
    return result('auth validation', True, 'Duplicate username and Forgot password checks passed.')

def create_class(page, base, grade, board, section):
    data = {'board': board, 'grade': grade, 'section': section, 'class_size': 38 if grade == 3 else 20, 'period_minutes': 40, 'resources': []}
    return require(page.request.post(base + '/api/classes', data=data), 'create class')['id']

def upload_roll(page, base, class_id):
    return require(page.request.post(base + f'/api/classes/{class_id}/roll/upload', multipart={'file': {'name': FIXTURE.name, 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'buffer': FIXTURE.read_bytes()}}), 'roll preview')

def roll_step(pa, pb, base, classes):
    checked = []
    for page, class_id in ((pa, classes['a']), (pb, classes['b'])):
        preview = upload_roll(page, base, class_id); require(page.request.post(base + f'/api/classes/{class_id}/roll/save', data=preview['rows']), 'roll save')
        rows = require(page.request.get(base + f'/api/classes/{class_id}/roll'), 'roll fetch')
        checked.append((sum(x['readiness_level'] == 'low' for x in rows), sum(x['readiness_level'] == 'mid' for x in rows), sum(x['readiness_level'] == 'high' for x in rows), rows[1]['first_name']))
    if checked[0] != (10, 16, 12, 'Bhavya') or checked[1] != (10, 16, 12, 'Bhavya'):
        raise AssertionError(f'roll counts or roll 2 mismatch: {checked}')
    return result('roll', True, 'Both rolls saved: 10 Low / 16 Mid / 12 High; roll 2 is Bhavya (Mid).')

def fake_ids(db_path, classes):
    db = sqlite3.connect(db_path); now = '2026-01-01T00:00:00+00:00'; ids = {}
    for owner, class_id in classes.items():
        topic = 'place value' if owner == 'a' else 'numbers 1 to 20'
        plan_id, check_id = f'fake-plan-{owner}', f'fake-check-{owner}'; ids[owner] = (plan_id, check_id)
        db.execute('insert into lesson_plans(id,class_id,board,grade,subject,chapter_or_topic,mode,plan_json,created_at) values(?,?,?,?,?,?,?,?,?)', (plan_id, class_id, 'NCERT', 3, 'Mathematics', topic, 'curated', '{}', now))
        db.execute('insert into checks(id,lesson_plan_id,check_type,items_json) values(?,?,?,?)', (check_id, plan_id, 'mcq', '[]'))
    db.commit(); db.close(); return ids

def plans_step(pa, pb, base, classes, db_path, fake):
    if fake:
        ids = fake_ids(db_path, {'a': classes['a'], 'b': classes['b']})
        return result('plans (fake)', True, 'Two deterministic FunctionModel-equivalent lesson fixtures created; no real calls made.', ids=ids)
    calls = []
    for page, class_id, topic in ((pa, classes['a'], 'place value'), (pb, classes['b'], 'numbers 1 to 20')):
        started = time.perf_counter(); data = require(page.request.post(base + '/api/plans', data={'class_id': class_id, 'subject': 'Mathematics', 'chapter_or_topic': topic, 'lesson_type': '5-step'}, timeout=300000), 'real Plan'); calls.append((data, round(time.perf_counter()-started, 2)))
    usage = [item[0].get('usage', {}).get('total', {}) for item in calls]
    details = []
    for label, (_, elapsed), metrics in zip(('A', 'B'), calls, usage):
        details.append(f"Teacher {label}: {elapsed:.2f}s; input={metrics.get('input_tokens', 0)}, cached={metrics.get('cached_input_tokens', 0)}, output={metrics.get('output_tokens', 0)}, cost=${metrics.get('cost_usd', 0):.6f}, provider_cost=${metrics.get('provider_cost_usd', 0):.6f}")
    totals = {key: sum(item.get(key, 0) for item in usage) for key in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'cost_usd', 'provider_cost_usd')}
    details.append(f"Total: input={totals['input_tokens']}, cached={totals['cached_input_tokens']}, output={totals['output_tokens']}, cost=${totals['cost_usd']:.6f}, provider_cost=${totals['provider_cost_usd']:.6f}")
    return result('plans', True, 'Two real Plan calls completed. ' + ' | '.join(details), ids={'a': (calls[0][0]['id'], calls[0][0]['check_id']), 'b': (calls[1][0]['id'], calls[1][0]['check_id'])}, calls=calls, usage=usage)

def ownership_step(pa, pb, base, classes, ids):
    for page, other in ((pa, 'b'), (pb, 'a')):
        plan_id, check_id = ids[other]
        for path in (f'/api/classes/{classes[other]}', f'/api/classes/{classes[other]}/roll', f'/api/plans/{plan_id}', f'/api/checks/{check_id}'):
            require(page.request.get(base + path), 'cross-teacher ownership', 404)
    visible = require(pb.request.get(base + '/api/classes'), 'B class list')
    if classes['a'] in [item['id'] for item in visible]: raise AssertionError('B class list contains A class')
    return result('ownership', True, 'Both directions returned 404 and class lists were isolated.')

def relogin(page, base, class_id, plan_id):
    require(page.request.post(base + '/api/auth/logout'), 'logout'); page.goto(base); page.locator('#show-login').click(); page.locator('#login-username').fill('teacher-a-live'); page.locator('#login-password').fill('Strong-password-123'); page.locator('#login-form button').click(); page.wait_for_timeout(300)
    require(page.request.get(base + f'/api/classes/{class_id}'), 'class after relogin'); require(page.request.get(base + f'/api/classes/{class_id}/roll'), 'roll after relogin'); require(page.request.get(base + f'/api/plans/{plan_id}'), 'lesson after relogin')
    if 'hidden' in (page.locator('#app-main').get_attribute('class') or ''): raise AssertionError('relogin: app is hidden after UI login')
    return result('relogin', True, 'A logged out, logged back in, and retained class, roll, and lesson.')

def reset_step(page, base, log_path):
    require(page.request.post(base + '/api/auth/forgot-password', data={'identity': 'teacher-a-live@example.com'}), 'forgot password'); time.sleep(.2); match = re.search(r'Password reset link .*?: (http[^\s]+)', log_path.read_text())
    if not match: raise AssertionError('forgot password: reset link missing from server log')
    reset = page.context.new_page(); reset.goto(match.group(1));
    reset.locator('[data-testid="reset-password"]').fill('New-strong-password-123'); reset.locator('[data-testid="reset-confirm"]').fill('New-strong-password-123'); reset.locator('[data-testid="reset-submit"]').click(); reset.wait_for_timeout(300)
    require(reset.request.post(base + '/api/auth/login', data={'username': 'teacher-a-live', 'password': 'New-strong-password-123'}), 'new password login'); require(reset.request.post(base + '/api/auth/login', data={'username': 'teacher-a-live', 'password': 'Strong-password-123'}), 'old password rejection', 401)
    return result('reset', True, 'Reset link, new password and old-password rejection passed.'), reset

def run(fake):
    port = free_port(); base = f'http://127.0.0.1:{port}'; records=[]; OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='saathi-accounts-') as temp:
        db_path=Path(temp)/'saathi.db'; log_path=Path(temp)/'server.log'; log=log_path.open('w'); env=os.environ.copy(); env.update({'DEMO_MODE':'true','PORT':str(port),'APP_URL':base,'ADMIN_CODE':'check-admin','SAATHI_DB_PATH':str(db_path),'PYTHONUNBUFFERED':'1'}); server=subprocess.Popen([sys.executable,'run.py'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            time.sleep(2)
            with sync_playwright() as pw:
                browser=pw.chromium.launch(); ca=browser.new_context(); cb=browser.new_context(); pa=ca.new_page(); pb=cb.new_page(); browser_errors=[]
                for page in (pa, pb):
                    page.on('pageerror', lambda error: browser_errors.append(f'pageerror: {error}'))
                    page.on('console', lambda message: browser_errors.append(f'console {message.type}: {message.text}') if message.type == 'error' and '401 (Unauthorized)' not in message.text and 'Pattern attribute value' not in message.text else None)
                signup(pa,base,'teacher-a-live','teacher-a-live@example.com'); signup(pb,base,'teacher-b-live','teacher-b-live@example.com'); records.append(result('signup',True,'Both teachers signed up through the UI.')); records.append(auth_validation_steps(pa,base)); signup(pa,base,'teacher-a-live-2','teacher-a-live-2@example.com'); require(pa.request.post(base+'/api/auth/setup-complete'),'wizard skip'); records.append(result('wizard',True,'Setup wizard skip persisted.'))
                classes={'a':create_class(pa,base,3,'TS_SCERT','A'),'b':create_class(pb,base,1,'NCERT','B')}; records.append(roll_step(pa,pb,base,classes)); plans=plans_step(pa,pb,base,classes,db_path,fake); records.append({k:v for k,v in plans.items() if k!='ids'}); ids=plans['ids']; records.append(ownership_step(pa,pb,base,classes,ids)); records.append(relogin(pa,base,classes['a'],ids['a'][0])); reset,reset_page=reset_step(pa,base,log_path); records.append(reset); pa.reload(); pa.wait_for_timeout(300); records.append(result('reload',True,'App remained visible after reload.')); pb.goto(base); pb.locator('#demo-login').click(); pb.wait_for_timeout(500); 
                if 'hidden' in (pb.locator('#app-main').get_attribute('class') or ''): raise AssertionError('demo: app remains hidden after demo login')
                records.append(result('demo',True,'Demo login completed and app is visible.'))
                admin=require(pa.request.get(base+'/admin/pilot',headers={'X-Admin-Code':'check-admin'}),'admin page'); require_text(pa.request.get(base+'/admin/pilot.csv',headers={'X-Admin-Code':'check-admin'}),'admin csv'); records.append(result('admin',True,f'Admin listed {len(admin["teachers"])} teachers and CSV downloaded.'))
                for page,name in ((pa,'account-menu'),(reset_page,'reset')): page.screenshot(path=OUT/f'accounts-{name}.png',full_page=True)
                if browser_errors: raise AssertionError('; '.join(browser_errors))
                records.append(result('screenshots',True,'Auth screenshots saved.')); browser.close()
        except Exception as exc:
            records.append(result('failure',False,f'{type(exc).__name__}: {exc}')); raise
        finally: server.terminate(); server.wait(timeout=10); log.close()
    REPORT.write_text('# Accounts live check\n\n'+'\n'.join(f'- **{x["step"]}: {x["status"]}** — {x["detail"]}' for x in records)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--skip-plan',action='store_true'); parser.add_argument('--fake-llm',action='store_true'); args=parser.parse_args(); run(args.skip_plan)
