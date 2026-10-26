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
'<section><h2>The problem</h2><p>Primary teachers prepare for tomorrow while children learn at different levels. A score alone does not say what to reteach. Saathi closes the loop from a lesson plan to a paper check to the next action.</p><div class="big">37–43</div><p>Children per pilot classroom; the three classes contained 38, 37, and 43 children.</p></section>',
'<section><h2>What is new</h2><div class="loop"><b>PLAN</b><b>→ CHECK</b><b>→ NEXT STEPS</b></div><ul><li>No student devices</li><li>Diagnosis and groups computed by code</li><li>Differentiated next lesson, not just a score</li></ul></section>',
'<section><h2>How it works</h2><svg viewBox="0 0 900 300" role="img" aria-label="Six-agent Saathi loop"><g fill="#f4ba55" stroke="#fffdf7" stroke-width="3" font-family="Arial" text-anchor="middle"><rect x="15" y="90" width="125" height="60" rx="16"/><rect x="160" y="90" width="125" height="60" rx="16"/><rect x="305" y="90" width="125" height="60" rx="16"/><rect x="450" y="90" width="125" height="60" rx="16"/><rect x="595" y="90" width="125" height="60" rx="16"/><rect x="740" y="90" width="145" height="60" rx="16"/></g><g fill="#123f39" font-size="16" text-anchor="middle" font-family="Arial"><text x="77" y="125">Planner</text><text x="222" y="125">Check Builder</text><text x="367" y="125">Reader</text><text x="512" y="125">Reviewer</text><text x="657" y="125">Coach</text><text x="812" y="125">Resources</text></g><path d="M75 205 C250 255 650 255 820 205" fill="none" stroke="#f4ba55" stroke-width="5"/><text x="450" y="290" fill="#fffdf7" font-size="18" text-anchor="middle">code marking · diagnosis · budgets · number checks</text></svg><p>Six prompted agents are orchestrated by plain Python. Code handles marking, readiness maths, support-child selection, and arithmetic validation.</p></section>',
f'<section><h2>From plan to check</h2><p class="small subtitle">Screens from the demo account with the sample answer sheets.</p><div class="twocol"><figure>{img("slides-plan-vision.png")}<figcaption>Lesson Vision: objective, why, assessment</figcaption></figure><figure>{img("slides-check-steps.png")}<figcaption>Check: choose the lesson, upload sheets, see the analysis</figcaption></figure></div></section>',
f'<section><h2>From results to action</h2><p class="small subtitle">Screens from the demo account with the sample answer sheets.</p><div class="twocol"><figure>{img("slides-next-insight.png")}<figcaption>Next steps: the most common errors, counted by code</figcaption></figure><figure>{img("slides-worksheet.png")}<figcaption>Worksheets at three readiness levels, with answers</figcaption></figure></div></section>',
f'<section><h2>Real trace: one full loop</h2><div class="big">46.6s</div><p>Plan · 5 sheets 10.9s · Next steps 29.4s · worksheet 6.7s</p><p>14 model calls · 14 tool calls · <b>$0.011 for the whole loop</b> (from evidence/run_trace.json). One planner revision and one Coach revision were recorded.</p></section>',
'<section><h2>Safety by design</h2><ul><li>401 without a session</li><li>404 for another teacher’s data</li><li>Lockout and daily budgets</li><li>Prompt and output safety checks</li></ul><div class="callout">No children’s names or real answer-sheet images are included here.</div></section>',
'<section><h2>Piloted with real data from three classrooms</h2><div class="big">3 · 118 · 590</div><p class="small">classrooms · children · answers read and marked</p><table><tr><th>Class</th><th>Children</th><th>Average</th><th>Low / Mid / High</th></tr><tr><td>Grade 2 TS</td><td>38</td><td>29.5%</td><td>40 / 26.3 / 25%</td></tr><tr><td>Grade 4 NCERT</td><td>37</td><td>81.1%</td><td>51.1 / 80 / 97.6%</td></tr><tr><td>Grade 5 TS</td><td>43</td><td>62.8%</td><td>38.8 / 71.1 / 88.9%</td></tr></table><p>Four feedback entries; mean rating 3.75. Anurag: “a blessing for a beginner teacher.”</p></section>',
'<section><h2>What comes next</h2><p>Verify chapter coverage, expand misconception libraries, add offline capture, and run a comparison-class pilot.</p><p>Run locally from the README.</p><a href="'+html.escape(REPO)+'">'+html.escape(REPO)+'</a><p class="small">The report documents the measured trace, pilot caveats, and evidence boundaries.</p></section>']
css="""
/* Saathi deck: every rule is scoped under .reveal so it never collides with reveal.js's own classes. */
@font-face{font-family:'Baloo 2';src:url(FONT_DATA) format('woff2');font-display:swap}
.reveal-viewport{background:#2F5D50}
.reveal{font-family:-apple-system,'Segoe UI',Arial,sans-serif;color:#FFFDF6;font-size:30px}
.reveal .slides{text-align:left}
.reveal .slides section{padding:46px 70px;height:720px;box-sizing:border-box}
.reveal h1,.reveal h2{font-family:'Baloo 2',-apple-system,Arial,sans-serif;font-weight:700;text-transform:none;letter-spacing:0;margin:0 0 26px}
.reveal h1{font-size:76px;line-height:1.02;color:#FFFDF6}
.reveal h2{font-size:52px;line-height:1.1;color:#F2A93B}
.reveal p,.reveal li{font-size:30px;line-height:1.35;max-width:1080px;margin:0 0 18px}
.reveal ul{margin:10px 0 0 34px}
.reveal a{color:#F2A93B;text-decoration:underline}
.reveal b{color:#F2A93B}
.reveal .title{display:flex;flex-direction:column;justify-content:center}
.reveal .title small{font-size:22px;letter-spacing:.2em;color:#F2A93B}
.reveal .title a{font-size:30px;margin-top:10px}
.reveal .big{font-family:'Baloo 2',Arial,sans-serif;font-size:118px;font-weight:700;line-height:1;color:#F2A93B;margin:10px 0 18px}
.reveal .loop{display:flex;gap:18px;flex-wrap:wrap;margin:24px 0 34px}
.reveal .loop b{background:#F2A93B;color:#2F5D50;padding:16px 26px;border-radius:20px;font-size:32px}
.reveal .twocol{display:grid;grid-template-columns:1fr 1fr;gap:26px;align-items:start}
.reveal .twocol img{width:100%;max-height:440px;object-fit:contain;border-radius:14px;border:3px solid #FFFDF6;margin:0;background:#FFFDF6}
.reveal figure{margin:0}.reveal figcaption{font-size:20px;margin-top:10px;opacity:.9}.reveal .callout{border:3px solid #F2A93B;padding:20px 24px;border-radius:14px;font-size:28px;margin-top:22px}
.reveal .subtitle{margin:-14px 0 18px}.reveal .small{font-size:20px;opacity:.85}
.reveal .missing{border:2px dashed #F2A93B;padding:70px;text-align:center}
.reveal svg{width:100%;max-height:300px;margin:0 0 18px}
.reveal table{border-collapse:collapse;font-size:26px;margin:6px 0 20px}
.reveal th,.reveal td{padding:8px 22px;border-bottom:1px solid rgba(255,253,246,.35);text-align:left}
.reveal th{color:#F2A93B}
.reveal .slide-number{background:rgba(0,0,0,.25);color:#FFFDF6}
.reveal .progress{color:#F2A93B}
.reveal .controls{color:#F2A93B}
"""
OUT=ROOT/'slides.html'
font=base64.b64encode((ROOT/'static/fonts/Baloo2-Regular.woff2').read_bytes()).decode()
css=css.replace('FONT_DATA', 'data:font/woff2;base64,'+font)
slides_markup=''.join(slides)
init="Reveal.initialize({hash:true,slideNumber:true,progress:true,center:false,width:1280,height:720,margin:0.04});"
OUT.write_text(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Saathi slides</title><link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css'><style>{css}</style></head><body><div class='reveal'><div class='slides'>{slides_markup}</div></div><script src='https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js'></script><script>{init}</script></body></html>")
print(OUT)
