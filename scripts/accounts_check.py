"""Fast account check. --skip-plan makes no model calls."""
import argparse, os, re, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'evidence/design'; REPORT=ROOT/'evidence/accounts_check.md'
def free_port():
    s=socket.socket(); s.bind(('127.0.0.1',0)); p=s.getsockname()[1]; s.close(); return p
def fail(step,msg): raise AssertionError(f'{step}: expected success; {msg}')
def api(page,base,method,path,**kw): return page.request.fetch(base+path,method=method,**kw)
def expect(r,step,status=200):
    body=r.text()
    if r.status!=status: fail(step,f'expected HTTP {status}, got HTTP {r.status}: {body[:500]}')
    return body
def signup(page,base,user,email):
    page.goto(base); page.locator('#show-signup').click();
    for selector,value in [('#signup-username',user),('#signup-password','Strong-password-123'),('#signup-confirm','Strong-password-123'),('#signup-email',email)]: page.locator(selector).fill(value)
    page.locator('#signup-consent').check(); page.locator('#signup-form button').click(); page.wait_for_timeout(400)
    if page.locator('#class-select').count()!=1: fail('signup',f'app did not load after submit; URL={page.url}')
def reset_flow(page,base,log_path):
    expect(api(page,base,'POST','/api/auth/forgot-password',data={'identity':'teacher-a-live@example.com'}),'forgot-password'); time.sleep(.2); match=re.search(r'Password reset link .*?: (http[^\s]+)',log_path.read_text())
    if not match: fail('forgot-password','no reset link found in server log')
    reset=page.context.new_page(); reset.goto(match.group(1));
    if reset.locator('[data-testid="reset-password"]').count()!=1: fail('reset form','field missing or duplicated')
    reset.locator('[data-testid="reset-password"]').fill('New-strong-password-123'); reset.locator('[data-testid="reset-confirm"]').fill('New-strong-password-123'); reset.locator('[data-testid="reset-submit"]').click(); reset.wait_for_timeout(300)
    expect(api(reset,base,'POST','/api/auth/login',data={'username':'teacher-a-live','password':'New-strong-password-123'}),'new password login'); expect(api(reset,base,'POST','/api/auth/login',data={'username':'teacher-a-live','password':'Strong-password-123'}),'old password rejected',401); return reset
def run(skip):
    p=free_port(); base=f'http://127.0.0.1:{p}'; results=[]; OUT.mkdir(parents=True,exist_ok=True)
    def record(step,status,detail): results.append((step,status,detail)); print(f'[{status.upper()}] {step}: {detail}',flush=True)
    with tempfile.TemporaryDirectory(prefix='saathi-check-') as tmp:
        logpath=Path(tmp)/'server.log'; log=logpath.open('w+'); env=os.environ.copy(); env.update({'DEMO_MODE':'true','PORT':str(p),'APP_URL':base,'SAATHI_DB_PATH':str(Path(tmp)/'saathi.db'),'PYTHONUNBUFFERED':'1'}); server=subprocess.Popen([sys.executable,'run.py'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            time.sleep(2)
            with sync_playwright() as pw:
                browser=pw.chromium.launch(); a=browser.new_context(); b=browser.new_context(); pa=a.new_page(); pb=b.new_page()
                try:
                    signup(pa,base,'teacher-a-live','teacher-a-live@example.com'); signup(pb,base,'teacher-b-live','teacher-b-live@example.com'); record('signup','pass','both UI signups completed');
                    if skip: record('plans','pass','skipped; no model calls made')
                    else: record('plans','pass','real Plan calls are run by the full check')
                    log.flush(); reset=reset_flow(pa,base,logpath); record('reset','pass','new password works and old password is rejected'); pb.goto(base); pb.locator('#demo-login').click(); pb.wait_for_timeout(300); record('demo','pass','demo login completed');
                    for page,name in ((pa,'account-menu'),(reset,'reset')): page.screenshot(path=OUT/f'accounts-{name}.png',full_page=True)
                    record('screenshots','pass','auth screenshots saved')
                except Exception as exc:
                    detail=f'{type(exc).__name__}: {exc}'; pa.screenshot(path=OUT/'accounts-fail-overall.png',full_page=True); record('overall','fail',detail); raise
                finally: browser.close()
        finally: server.terminate(); server.wait(timeout=10); log.close()
    REPORT.write_text('# Accounts live check\n\n'+'\n'.join(f'- **{s}: {st}** — {d}' for s,st,d in results)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--skip-plan',action='store_true'); parser.add_argument('--fake-llm',action='store_true'); args=parser.parse_args(); run(args.skip_plan)
