const state = { boards: [], classes: [], currentResult: null };
const $ = (id) => document.getElementById(id);

function addText(parent, tag, text, className = '') {
  const element = document.createElement(tag);
  element.textContent = text == null ? '' : String(text);
  if (className) element.className = className;
  parent.appendChild(element);
  return element;
}

async function getJson(url, options) {
  options = options || {};
  options.headers = Object.assign({}, options.headers || {}, {
    'X-Saathi-Access-Code': localStorage.getItem('saathi_access_code') || ''
  });
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'The request could not be completed.');
  return data;
}

function selectedClass() {
  return state.classes.find((item) => item.id === $('class-select').value);
}

function refreshSubjects() {
  const current = selectedClass();
  $('subject-select').replaceChildren();
  if (!current) return;
  const board = state.boards.find((item) => item.id === current.board);
  const grade = board?.grades.find((item) => item.grade === current.grade);
  (grade?.subjects || []).forEach((subject) => {
    const option = document.createElement('option');
    option.value = subject.name;
    option.textContent = subject.name;
    $('subject-select').appendChild(option);
  });
  refreshChapters();
}

function refreshChapters() {
  const current = selectedClass();
  const board = state.boards.find((item) => item.id === current?.board);
  const grade = board?.grades.find((item) => item.grade === current?.grade);
  const subject = grade?.subjects.find((item) => item.name === $('subject-select').value);
  $('chapter-select').replaceChildren(new Option('Type a chapter or topic', ''));
  (subject?.chapters || []).forEach((chapter) => $('chapter-select').add(new Option(chapter.title, chapter.title)));
}

function renderClasses() {
  $('class-select').replaceChildren();
  state.classes.forEach((item) => {
    const option = new Option(`Grade ${item.grade}${item.section} · ${item.board === 'TS_SCERT' ? 'Telangana' : 'NCERT'}`, item.id);
    $('class-select').add(option);
  });
  refreshSubjects();
}

function renderError(message) {
  const result = $('plan-result');
  result.replaceChildren();
  const card = addText(result, 'div', '', 'card error');
  addText(card, 'h3', 'Something went wrong');
  addText(card, 'p', message);
}

function renderUsageStrip(result) {
  const usage = result.usage.total;
  const strip = addText(document.createElement('div'), 'div', '', 'usage-strip');
  addText(strip, 'span', `Input ${usage.input_tokens}`);
  addText(strip, 'span', `Cached ${usage.cached_input_tokens}`);
  addText(strip, 'span', `Output ${usage.output_tokens}`);
  addText(strip, 'span', `Project cost $${usage.cost_usd.toFixed(6)}`);
  addText(strip, 'span', `Provider cost $${usage.provider_cost_usd.toFixed(6)}`);
  return strip;
}

function renderCheck(parent, result) {
  addText(parent, 'h3', result.check_type === 'mcq' ? 'Exit check' : 'Observation check');
  const toggle = document.createElement('button');
  toggle.className = 'secondary';
  toggle.textContent = 'Show common errors';
  parent.appendChild(toggle);
  const errors = [];
  const checkItems = result.check.questions || result.check.tasks || [];
  checkItems.forEach((item, index) => {
    const card = addText(parent, 'article', '', 'check-card');
    addText(card, 'h4', `${index + 1}. ${item.stem || item.task}`);
    if (item.options) Object.entries(item.options).forEach(([letter, text]) => addText(card, 'p', `${letter}. ${text}${letter === item.correct_option ? ' ✓' : ''}`, letter === item.correct_option ? 'correct' : ''));
    if (item.materials) addText(card, 'p', `Materials: ${item.materials.join(', ')}`);
    if (item.what_success_looks_like) addText(card, 'p', `Success looks like: ${item.what_success_looks_like}`);
    const itemErrors = Object.values(item.option_errors || {}).concat(item.common_errors || []);
    itemErrors.forEach((error) => errors.push(error));
  });
  const errorBox = addText(parent, 'div', '', 'common-errors hidden');
  errors.forEach((error) => { const row = addText(errorBox, 'p', error.description); if (error.ai_suggested) addText(row, 'small', ' AI-suggested', 'tag'); });
  toggle.addEventListener('click', () => { errorBox.classList.toggle('hidden'); toggle.textContent = errorBox.classList.contains('hidden') ? 'Show common errors' : 'Hide common errors'; });
}

function renderResult(result) {
  state.currentResult = result;
  const root = $('plan-result');
  root.replaceChildren();
  const card = addText(root, 'div', '', 'result card');
  const badges = addText(card, 'div', '', 'badges');
  addText(badges, 'span', result.mode === 'curated' ? 'Curated' : 'Open', 'badge');
  addText(badges, 'span', result.review.passed ? 'Checked ✓' : 'Issues found', 'badge');
  if (result.revised) addText(badges, 'span', 'Revised once', 'badge accent');
  addText(card, 'h2', result.plan.title);
  addText(card, 'h3', 'Learning objectives');
  result.plan.learning_objectives.forEach((item) => addText(card, 'p', item));
  addText(card, 'h3', 'Materials');
  addText(card, 'p', result.plan.materials.join(', '));
  addText(card, 'h3', 'Lesson sections');
  result.plan.sections.forEach((section) => { const sectionCard = addText(card, 'article', '', 'section-card'); addText(sectionCard, 'h4', `${section.name} · ${section.minutes} minutes`); addText(sectionCard, 'p', `Teacher: ${section.teacher_actions.join(' ')}`); addText(sectionCard, 'p', `Children: ${section.student_actions.join(' ')}`); });
  addText(card, 'h3', 'Local examples'); addText(card, 'p', result.plan.local_examples.join(', '));
  addText(card, 'h3', 'Large-class tips'); result.plan.large_class_tips.forEach((tip) => addText(card, 'p', tip));
  addText(card, 'h3', 'Differentiation'); addText(card, 'p', `Support: ${result.plan.differentiation_tips.support}`); addText(card, 'p', `On level: ${result.plan.differentiation_tips.on_level}`); addText(card, 'p', `Challenge: ${result.plan.differentiation_tips.challenge}`);
  addText(card, 'h3', 'Home activity'); addText(card, 'p', result.plan.homework_or_home_activity);
  renderCheck(card, result);
  if (result.review.issues.length) { addText(card, 'h3', 'Review issues'); result.review.issues.forEach((issue) => addText(card, 'p', `${issue.target}: ${issue.problem} Fix: ${issue.fix}`)); }
  card.appendChild(renderUsageStrip(result));
  const actions = addText(card, 'div', '', 'actions');
  const print = addText(actions, 'button', 'Print', 'secondary'); print.onclick = () => window.print();
  const chalkboard = addText(actions, 'button', 'Chalkboard version', 'secondary'); chalkboard.onclick = () => openChalkboard(result);
}

function openChalkboard(result) {
  const popup = window.open('', '_blank');
  if (!popup) return;
  popup.document.title = 'Saathi chalkboard version';
  const style = popup.document.createElement('style');
  style.textContent = 'body{font-family:system-ui;padding:8vw;font-size:clamp(2rem,5vw,4rem);line-height:1.3}h1{font-size:1.2em}li{margin:1em 0}';
  popup.document.head.appendChild(style);
  const root = popup.document.body;
  const title = popup.document.createElement('h1'); title.textContent = result.plan.title; root.appendChild(title);
  const items = result.check.questions || result.check.tasks || [];
  const list = popup.document.createElement('ol');
  items.forEach((item) => { const li = popup.document.createElement('li'); li.textContent = item.stem || item.task; list.appendChild(li); });
  root.appendChild(list);
}

async function loadUsage() {
  const data = await getJson('/api/usage');
  $('usage-summary').replaceChildren();
  const totals = data.totals;
  addText($('usage-summary'), 'p', `${totals.runs} runs · ${totals.input_tokens} input · ${totals.cached_input_tokens} cached · ${totals.output_tokens} output · $${totals.cost_usd.toFixed(6)} project cost · $${totals.provider_cost_usd.toFixed(6)} provider cost`);
  const agents = addText($('usage-summary'), 'div', '', 'agent-breakdown');
  data.per_agent.forEach((agent) => addText(agents, 'p', `${agent.agent_name}: ${agent.input_tokens} in · ${agent.cached_input_tokens} cached · ${agent.output_tokens} out · $${Number(agent.cost_usd).toFixed(6)} project / $${Number(agent.provider_cost_usd).toFixed(6)} provider`));
  $('usage-rows').replaceChildren();
  data.recent_runs.forEach((run) => { const row = $('usage-rows').insertRow(); [new Date(run.created_at).toLocaleString(), run.class_name || run.class_id, run.status, '—', '—', '—', `$${Number(run.total_cost_usd || 0).toFixed(6)}`].forEach((value) => addText(row.insertCell(), 'span', value)); });
}

async function load() {
  const health = await getJson('/api/health');
  if (health.access_required && !localStorage.getItem('saathi_access_code')) {
    const code = window.prompt('Enter the Saathi access code');
    if (code) localStorage.setItem('saathi_access_code', code);
  }
  const [boards, classes] = await Promise.all([getJson('/api/boards'), getJson('/api/classes')]);
  state.boards = boards.boards; state.classes = classes; renderClasses();
  $('key-status').classList.toggle('ready', health.key_found); $('key-status').title = health.key_found ? 'Portkey key ready' : health.message;
}

$('class-select').addEventListener('change', refreshSubjects); $('subject-select').addEventListener('change', refreshChapters);
$('topic-input').addEventListener('input', (event) => $('topic-count').textContent = `${event.target.value.length} / 120`);
$('note-input').addEventListener('input', (event) => $('note-count').textContent = `${event.target.value.length} / 500`);
$('plan-form').addEventListener('submit', async (event) => { event.preventDefault(); $('prepare-button').disabled = true; $('progress').classList.remove('hidden'); try { const result = await getJson('/api/plans', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({class_id: $('class-select').value, subject: $('subject-select').value, chapter_or_topic: $('topic-input').value, teacher_note: $('note-input').value}) }); if (result.error) renderError(result.error); else renderResult(result); } catch (error) { renderError(error.message); } finally { $('prepare-button').disabled = false; $('progress').classList.add('hidden'); } });
$('add-class-button').onclick = () => $('class-dialog').showModal(); $('close-dialog').onclick = () => $('class-dialog').close();
$('class-form').addEventListener('submit', async (event) => { event.preventDefault(); const resources = [...document.querySelectorAll('#class-form input[type=checkbox]:checked')].map((item) => item.value); const created = await getJson('/api/classes', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({board:$('new-board').value, grade:Number($('new-grade').value), section:$('new-section').value, class_size:Number($('new-size').value), period_minutes:Number($('new-period').value), resources})}); state.classes = await getJson('/api/classes'); renderClasses(); $('class-select').value = created.id; refreshSubjects(); $('class-dialog').close(); });
document.querySelectorAll('.tabs button').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('.tabs button').forEach((item) => item.classList.remove('active')); button.classList.add('active'); document.querySelectorAll('.view').forEach((view) => view.classList.add('hidden')); $(button.dataset.view).classList.remove('hidden'); if (button.dataset.view === 'usage-view') loadUsage(); }));
load();
