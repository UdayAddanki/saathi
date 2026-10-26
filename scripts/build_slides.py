"""Build a self-contained ten-slide deck from committed evidence."""
from __future__ import annotations
import base64, html, json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=os.environ.get('REPO_URL','{{REPO_URL}}')
if REPO=='{{REPO_URL}}': raise SystemExit('Set REPO_URL before building slides')
data=json.loads((ROOT/'evidence/tokenomics.json').read_text())
def image(name):
 p=ROOT/'evidence/design'/name
 return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode() if p.exists() else ''
def img(name):
 s=image(name)
 return f'<img src="{s}">' if s else '<div class="missing">Screenshot placeholder</div>'
plan=data['run_types'].get('plan',{}); ns=data['run_types'].get('next_steps',{})
slides=[
f'<section class="title"><small>SAATHI · UDAY ADDANKI</small><h1>Plan the lesson.<br>Check who learned.<br>Know what to do next.</h1><p>Teacher copilot for India’s primary classrooms · no student devices</p><a href="{html.escape(REPO)}">{html.escape(REPO)}</a></section>',
'<section><h2>The problem</h2><p>Primary teachers prepare for tomorrow while children learn at different levels. A score alone does not say what to reteach. Saathi closes the loop from a lesson plan to a paper check to the next action.</p><div class="big">35–50</div><p>Typical classroom size: insert a verified source before submission.</p></section>',
'<section><h2>What is new</h2><div class="loop"><b>PLAN</b><b>→ CHECK</b><b>→ NEXT STEPS</b></div><ul><li>No student devices</li><li>Diagnosis and groups computed by code</li><li>Differentiated next lesson, not just a score</li></ul></section>',
'<section><h2>How it works</h2><p>Lesson Planner · Check Builder · Answer Sheet Reader · Reviewer · Next-Step Coach · Resource Builder</p><div class="flow">Prompted agents + deterministic code checks + budgets + ownership</div><p>Code handles marking, readiness maths, support-child selection, and arithmetic validation.</p></section>',
f'<section><h2>From Plan to Check</h2><div class="twocol">{img("plan-form-laptop-1280x800.png")}{img("check-laptop-1280x800.png")}</div></section>',
f'<section><h2>From results to action</h2><div class="twocol">{img("next-steps-laptop-1280x800.png")}{img("additional-resources-laptop-1280x800.png")}</div></section>',
f'<section><h2>Measured tokenomics</h2><div class="big">{plan.get("duration_ms",0)/1000:.1f}s</div><p>Average recorded Plan run · {plan.get("input_tokens",0):,.0f} input tokens · ${plan.get("cost_usd",0):.4f}</p><p>Next steps: {ns.get("input_tokens",0):,.0f} input tokens · ${ns.get("cost_usd",0):.4f}. Monthly scenarios require an explicit usage assumption.</p></section>',
'<section><h2>Safety by design</h2><ul><li>401 without a session</li><li>404 for another teacher’s data</li><li>Lockout and daily budgets</li><li>Prompt and output safety checks</li></ul><div class="callout">No children’s names or real answer-sheet images are included here.</div></section>',
'<section><h2>Piloted with real data from three classrooms</h2><div class="big">3 · 118 · 590</div><p>Classroom papers · uploaded sheets · answers read (verified evidence database totals). Four feedback entries were recorded; mean rating 3.75. These are observations, not proof of causality or teacher adoption.</p></section>',
'<section><h2>What comes next</h2><p>Verify chapter coverage, expand misconception libraries, add offline capture, and run a comparison-class pilot.</p><p>Run locally from the README.</p><a href="'+html.escape(REPO)+'">'+html.escape(REPO)+'</a><p class="small">Placeholder: add cited public statistics, final full-loop trace, diagnosis experiment, revision comparison, and hosting estimate if required.</p></section>']
css="""*{box-sizing:border-box}body{margin:0;background:#123f39;color:#fffdf7;font-family:Arial,sans-serif}.deck{height:100vh}.slide{display:none;min-height:100vh;padding:8vh 10vw}.slide.active{display:block}h1{font-size:clamp(38px,6vw,82px);line-height:1.03;margin:30px 0}h2{font-size:clamp(32px,5vw,62px);margin:0 0 35px;color:#f4ba55}p,li{font-size:clamp(18px,2.2vw,30px);line-height:1.35;max-width:900px}a{color:#f4ba55}.title{display:flex;flex-direction:column;justify-content:center}.title small{letter-spacing:.2em;color:#f4ba55}.big{font-size:clamp(65px,12vw,150px);font-weight:bold;color:#f4ba55}.loop,.flow{display:flex;gap:18px;flex-wrap:wrap;margin:40px 0}.loop b,.flow{background:#f4ba55;color:#123f39;padding:16px 22px;border-radius:20px}.twocol{display:grid;grid-template-columns:1fr 1fr;gap:25px}.twocol img{max-width:100%;max-height:55vh;border-radius:14px}.callout{border:2px solid #f4ba55;padding:20px;border-radius:14px}.small{font-size:14px}.missing{border:2px dashed #f4ba55;padding:70px;text-align:center}@media(max-width:700px){.twocol{grid-template-columns:1fr}}"""
js="""let i=0;const s=[...document.querySelectorAll('.slide')];function show(n){i=(n+s.length)%s.length;s.forEach((x,j)=>x.classList.toggle('active',j===i));}document.addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key))show(i+1);if(['ArrowLeft','PageUp'].includes(e.key))show(i-1)});show(0);"""
OUT=ROOT/'slides.html'
OUT.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>Saathi slides</title><style>{css}</style></head><body><main class='deck'>{''.join('<article class=\"slide\">'+s+'</article>' for s in slides)}</main><script>{js}</script></body></html>")
print(OUT)
