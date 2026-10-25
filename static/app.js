const state = { boards: [], classes: [], currentResult: null, rollPreviewInvalid: false, rollPreviewRows: null };
state.check = null;
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
  $('chapter-list').replaceChildren();
  (subject?.chapters || []).forEach((chapter) => $('chapter-list').appendChild(new Option(chapter.title, chapter.title)));
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
  if (result.plan.vision && result.plan.method) {
    const vision = addText(card, 'section', '', 'vision-card');
    addText(vision, 'h2', 'Lesson Vision');
    addText(vision, 'h3', 'Objective'); addText(vision, 'p', result.plan.vision.objective, 'objective');
    addText(vision, 'h3', 'Why this objective'); addText(vision, 'p', result.plan.vision.why_this_objective);
    addText(vision, 'h3', 'Assessment'); addText(vision, 'p', result.plan.vision.assessment);
    addText(vision, 'h3', 'Expected student response'); addText(vision, 'p', JSON.stringify(result.plan.vision.expected_student_response));
    const words = addText(vision, 'div', '', 'keyword-chips'); result.plan.vision.key_words.forEach((word) => addText(words, 'span', word.word, 'badge'));
    addText(card, 'h2', 'Lesson Method'); addText(card, 'p', `Lesson model: ${result.plan.lesson_type}`);
    result.plan.method.forEach((step) => { const section = addText(card, 'details', '', 'section-card'); const summary = addText(section, 'summary', `${step.name} · ${step.minutes} minutes`); addText(section, 'p', step.purpose); addText(section, 'p', `Materials: ${step.materials.join(', ')}`); const table = addText(section, 'div', '', 'exchange-table'); step.exchanges.forEach((exchange) => { addText(table, 'div', `Teacher: ${exchange.teacher}`, 'teacher-line'); addText(table, 'div', `Students: ${exchange.students}`, 'student-line'); }); });
    if (result.plan.project_outline) { addText(card, 'h3', 'Project outline'); result.plan.project_outline.days.forEach((day, index) => addText(card, 'p', `${index + 1}${index + 1 === result.plan.project_outline.today_day ? ' · Today' : ''}: ${day}`)); }
    renderCheck(card, result); card.appendChild(renderUsageStrip(result)); return;
  }
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

async function loadLessons() {
  const lessons = await getJson('/api/lessons/recent');
  $('lesson-select').replaceChildren();
  lessons.forEach((lesson) => $('lesson-select').add(new Option(`${lesson.class_name} · ${lesson.chapter_or_topic}`, lesson.check_id)));
  if (lessons.length) await loadCheck(lessons[0].check_id);
}

async function loadCheck(checkId) {
  if (!checkId) return;
  state.check = await getJson(`/api/checks/${checkId}`);
  const editor = $('check-editor'); editor.replaceChildren();
  const items = state.check.items.questions || state.check.items.tasks || [];
  state.check.itemsList = items;
  state.check.values = {};
  const header = addText(editor, 'div', '', 'response-header');
  addText(header, 'strong', 'Child / roll');
  items.forEach((_, index) => addText(header, 'strong', state.check.check_type === 'mcq' ? `Q${index + 1}` : `T${index + 1}`));
  state.check.students.forEach((student) => {
    const row = addText(editor, 'div', '', 'response-row');
    const identity = addText(row, 'div', '', 'child-identity');
    addText(identity, 'strong', `${student.roll_no}. ${student.first_name || ''}`);
    const absent = document.createElement('input');
    absent.type = 'checkbox'; absent.title = 'Absent'; absent.className = 'absent-toggle';
    absent.onchange = () => {
      row.classList.toggle('row-absent', absent.checked);
      Object.values(state.check.values).filter((entry) => entry.roll === student.roll_no).forEach((entry) => {
        entry.button.dataset.value = absent.checked ? 'absent' : (state.check.check_type === 'mcq' ? 'A' : 'got_it');
        entry.button.textContent = absent.checked ? '—' : (state.check.check_type === 'mcq' ? 'A' : '✓');
      });
    };
    identity.appendChild(absent);
    items.forEach((item, index) => {
      const button = addText(row, 'button', state.check.check_type === 'mcq' ? 'A' : '✓', 'response-cell');
      button.dataset.value = state.check.check_type === 'mcq' ? 'A' : 'got_it';
      button.onclick = () => cycleResponse(button, state.check.check_type);
      button.roll = student.roll_no; button.itemIndex = index;
      state.check.values[`${student.roll_no}-${index}`] = {button, roll: student.roll_no, item, index};
      if (state.check.check_type === 'observation') addErrorPicker(row, button, item);
    });
  });
  $('sample-results').classList.toggle('hidden', !state.demoMode);
}

function addErrorPicker(row, button, item) {
  const picker = document.createElement('select');
  picker.className = 'error-picker hidden'; picker.add(new Option('Error seen', ''));
  (item.common_errors || []).forEach((error) => picker.add(new Option(error.description, error.misconception_id || error.description)));
  picker.onchange = () => { button.errorId = picker.value; };
  button.addEventListener('click', () => picker.classList.toggle('hidden', !['partly', 'not_yet'].includes(button.dataset.value)));
  row.appendChild(picker);
}

function cycleResponse(button, type) {
  const values = type === 'mcq' ? ['A', 'B', 'C', 'D'] : ['got_it', 'partly', 'not_yet'];
  const next = values[(values.indexOf(button.dataset.value) + 1) % values.length];
  button.dataset.value = next; button.textContent = type === 'mcq' ? next : ({got_it:'✓', partly:'~', not_yet:'✗'}[next]);
  button.classList.toggle('wrong', next !== 'A' && next !== 'got_it');
}

function collectResponses() {
  const responses = [];
  Object.entries(state.check.values).forEach(([key, entry]) => {
    const button = entry.button;
    const [roll_no, item_index] = key.split('-').map(Number);
    const response = {roll_no, item_index};
    if (state.check.check_type === 'mcq') response.chosen_option = button.dataset.value;
    else { response.rating = button.dataset.value; response.error_id = button.errorId || null; }
    responses.push(response);
  });
  return responses;
}

function fillSampleResults() {
  if (!state.check) return;
  const items = state.check.itemsList;
  Object.values(state.check.values).forEach((entry) => {
    const button = entry.button;
    const roll = entry.roll;
    if (roll >= 30 && roll <= 32) {
      button.dataset.value = 'absent'; button.textContent = '—'; return;
    }
    if (state.check.check_type === 'observation') {
      const value = (roll + entry.index) % 5 === 0 ? 'not_yet' : ((roll + entry.index) % 3 === 0 ? 'partly' : 'got_it');
      button.dataset.value = value; button.textContent = {got_it:'✓', partly:'~', not_yet:'✗'}[value]; return;
    }
    const item = items[entry.index];
    const wrongOptions = Object.keys(item.option_errors || {});
    const shouldBeWrong = (roll + entry.index) % 3 === 0;
    const errorIndex = (roll + entry.index) % 9 === 0 && wrongOptions.length > 1 ? 1 : 0;
    const option = shouldBeWrong && wrongOptions.length ? wrongOptions[errorIndex] : item.correct_option;
    button.dataset.value = option; button.textContent = option;
  });
}

function renderClassCounts() {
  const editor = $('check-editor'); editor.replaceChildren();
  addText(editor, 'p', 'Class count mode gives class-level diagnosis only; it does not create child groups.');
  state.check.countInputs = [];
  state.check.itemsList.forEach((item, index) => {
    const card = addText(editor, 'div', '', 'count-card');
    addText(card, 'strong', `${state.check.check_type === 'mcq' ? 'Question' : 'Task'} ${index + 1}`);
    const inputs = {};
    const labels = state.check.check_type === 'mcq' ? ['A', 'B', 'C', 'D'] : ['got_it', 'partly', 'not_yet'];
    labels.forEach((label) => { const wrapper = addText(card, 'label', label); const input = document.createElement('input'); input.type = 'number'; input.min = 0; input.value = 0; input.dataset.label = label; wrapper.appendChild(input); inputs[label] = input; });
    state.check.countInputs.push(inputs);
  });
}

function collectClassCounts() {
  return Object.fromEntries(state.check.countInputs.map((inputs, index) => [index, Object.fromEntries(Object.entries(inputs).map(([label, input]) => [label, Number(input.value) || 0]))]));
}

async function load() {
  const health = await getJson('/api/health');
  if (health.access_required && !localStorage.getItem('saathi_access_code')) {
    const code = window.prompt('Enter the Saathi access code');
    if (code) localStorage.setItem('saathi_access_code', code);
  }
  const [boards, classes] = await Promise.all([getJson('/api/boards'), getJson('/api/classes')]);
  state.boards = boards.boards; state.classes = classes; state.demoMode = health.demo_mode; renderClasses();
  $('key-status').classList.toggle('ready', health.key_found); $('key-status').title = health.key_found ? 'Portkey key ready' : health.message;
  await loadContext();
}

async function loadContext() {
  const current = selectedClass();
  if (!current) return;
  const context = await getJson(`/api/classes/${current.id}/context`);
  $('current-situation').value = context.current_situation || context.learning_level_text || '';
  $('classroom-vision').value = context.classroom_vision || '';
  $('unit-goal').value = context.unit_goal || '';
}

$('class-select').addEventListener('change', () => { refreshSubjects(); loadContext(); if (!$('check-view').classList.contains('hidden')) loadRoll().catch((error) => showRollMessage(error.message, 'error')); }); $('subject-select').addEventListener('change', refreshChapters);
$('topic-input').addEventListener('input', (event) => $('topic-count').textContent = `${event.target.value.length} / 120`);
$('note-input').addEventListener('input', (event) => $('note-count').textContent = `${event.target.value.length} / 500`);
$('current-situation').addEventListener('input', (event) => $('situation-count').textContent = `${event.target.value.length} / 500`);
$('classroom-vision').addEventListener('input', (event) => $('vision-count').textContent = `${event.target.value.length} / 300`);
$('unit-goal').addEventListener('input', (event) => $('goal-count').textContent = `${event.target.value.length} / 300`);
$('chapter-pdf').addEventListener('change', async (event) => { const file = event.target.files[0]; if (!file) return; if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) { event.target.value = ''; $('upload-status').textContent = 'Please choose a PDF file.'; return; } if (file.size > 10 * 1024 * 1024) { event.target.value = ''; $('upload-status').textContent = 'That PDF is larger than 10 MB.'; return; } const data = new FormData(); data.append('file', file); try { const response = await fetch(`/api/classes/${$('class-select').value}/chapter-document`, {method:'POST', headers:{'X-Saathi-Access-Code': localStorage.getItem('saathi_access_code') || ''}, body:data}); const result = await response.json(); $('upload-status').textContent = response.ok ? `Attached: ${result.filename}` : (result.detail || 'The PDF could not be attached.'); } catch { $('upload-status').textContent = 'The PDF could not be attached.'; } });
function chooseLessonType(value) { document.querySelectorAll('.lesson-type').forEach((item) => item.classList.toggle('selected', item.dataset.lesson === value)); $('project-fields').classList.toggle('hidden', value !== 'project-based'); if (value === 'experiential') { $('day-number').value = 1; $('total-days').value = 1; } }
document.querySelectorAll('.lesson-type').forEach((button) => button.addEventListener('click', () => chooseLessonType(button.dataset.lesson)));
$('differentiated').addEventListener('change', (event) => $('differentiation-fields').classList.toggle('hidden', !event.target.checked));
$('plan-form').addEventListener('submit', async (event) => { event.preventDefault(); $('prepare-button').disabled = true; $('progress').classList.remove('hidden'); try { const lessonType = document.querySelector('.lesson-type.selected').dataset.lesson; const result = await getJson('/api/plans', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({class_id: $('class-select').value, subject: $('subject-select').value, chapter: $('chapter-input').value, topic: $('topic-input').value, lesson_type: lessonType, current_situation: $('current-situation').value, classroom_vision: $('classroom-vision').value, unit_goal: $('unit-goal').value, differentiated: $('differentiated').checked, differentiation_types: [...document.querySelectorAll('.diff-type:checked')].map((item) => item.value), use_last_groups: $('use-last-groups').checked, day_number: Number($('day-number').value), total_days: Number($('total-days').value), project_idea: $('project-idea').value, project_scope: $('project-scope').value, teacher_note: $('note-input').value}) }); if (result.error) renderError(result.error); else renderResult(result); } catch (error) { renderError(error.message); } finally { $('prepare-button').disabled = false; $('progress').classList.add('hidden'); } });
$('add-class-button').onclick = () => $('class-dialog').showModal(); $('close-dialog').onclick = () => $('class-dialog').close();
$('class-form').addEventListener('submit', async (event) => { event.preventDefault(); const resources = [...document.querySelectorAll('#class-form input[type=checkbox]:checked')].map((item) => item.value); const created = await getJson('/api/classes', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({board:$('new-board').value, grade:Number($('new-grade').value), section:$('new-section').value, class_size:Number($('new-size').value), period_minutes:Number($('new-period').value), resources})}); state.classes = await getJson('/api/classes'); renderClasses(); $('class-select').value = created.id; refreshSubjects(); $('class-dialog').close(); });
document.querySelectorAll('.tabs button').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('.tabs button').forEach((item) => item.classList.remove('active')); button.classList.add('active'); document.querySelectorAll('.view').forEach((view) => view.classList.add('hidden')); $(button.dataset.view).classList.remove('hidden'); if (button.dataset.view === 'usage-view') loadUsage(); }));
load();
$('lesson-select').addEventListener('change', (event) => loadCheck(event.target.value));
$('save-results').addEventListener('click', async () => { if (!state.check) return; const payload = state.check.mode === 'class_count' ? {check_mode:'class_count', class_counts:collectClassCounts()} : {check_mode:'each_child', responses:collectResponses()}; await getJson(`/api/checks/${state.check.id}/responses`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); alert('Results saved. Open Next steps to see the diagnosis.'); });
$('sample-results').addEventListener('click', fillSampleResults);
$('each-child-mode').addEventListener('click', () => { state.check.mode = 'each_child'; loadCheck(state.check.id); });
$('class-count-mode').addEventListener('click', () => { state.check.mode = 'class_count'; renderClassCounts(); });
document.querySelector('[data-view="check-view"]').addEventListener('click', loadLessons);
document.querySelector('[data-view="next-view"]').addEventListener('click', async () => { if (!state.check) return; const result = await getJson(`/api/checks/${state.check.id}/next-steps`, {method:'POST'}); const content = $('next-content'); content.replaceChildren(); addText(content, 'h3', 'Class insight'); result.insight.concepts.forEach((concept) => addText(content, 'p', `${concept.concept_id}: ${concept.percent_correct}% · ${concept.status}`)); addText(content, 'h3', 'Top errors'); result.insight.top_errors.slice(0, 3).forEach((error) => addText(content, 'p', `${error.count} children: ${error.description}${error.ai_suggested ? ' (AI-suggested)' : ''}`)); addText(content, 'h3', 'Coach summary'); addText(content, 'p', result.next_steps.summary); addText(content, 'h3', 'Next lesson warm-up'); addText(content, 'p', result.next_steps.next_lesson_warmup); const warmup = addText(content, 'button', 'Use in next lesson', 'primary'); warmup.onclick = async () => { await getJson(`/api/checks/${state.check.id}/use-warmup`, {method:'POST'}); warmup.textContent = 'Added to next lesson ✓'; warmup.disabled = true; }; const history = await getJson(`/api/progress/${selectedClass().id}`); const progress = $('progress-history'); progress.replaceChildren(); Object.entries(history.concepts).forEach(([concept, checks]) => { const row = addText(progress, 'p', `${concept}: `); checks.forEach((item) => addText(row, 'span', `${item.percent}%`, `progress-${item.status.replaceAll(' ', '-').toLowerCase()}`)); }); });

// The roll editor deliberately uses textContent for names and imported values.
async function loadRoll() {
  const roll = await getJson(`/api/classes/${selectedClass().id}/roll`);
  const columns = $('roll-columns'); columns.replaceChildren();
  for (const level of ['low', 'mid', 'high']) {
    const section = addText(columns, 'section', '', `roll-column roll-${level}`);
    addText(section, 'h3', `${level[0].toUpperCase() + level.slice(1)} readiness`);
    roll.filter((child) => child.readiness_level === level).forEach((child) => addText(section, 'p', `${child.roll_no}. ${child.first_name || 'Unnamed'}`));
  }
  let table = $('saved-roll-table');
  if (!table) { table = document.createElement('table'); table.id = 'saved-roll-table'; $('roll-columns').after(table); }
  table.replaceChildren();
  const header = table.insertRow(); ['Roll number', 'Name', 'Readiness level'].forEach((label) => { const cell = document.createElement('th'); cell.textContent = label; header.append(cell); });
  roll.forEach((child) => { const row = table.insertRow(); [child.roll_no, child.first_name || '', child.readiness_level].forEach((value) => { const cell = document.createElement('td'); cell.textContent = value; row.append(cell); }); });
}
function showRollMessage(message, kind = 'success') {
  let box = $('roll-message');
  if (!box) { box = document.createElement('p'); box.id = 'roll-message'; $('roll-columns').after(box); }
  box.textContent = message;
  box.className = `roll-message ${kind}`;
}
function showRollPreview(rows) {
  const columns = $('roll-columns'); columns.replaceChildren();
  for (const level of ['low', 'mid', 'high']) {
    const section = addText(columns, 'section', '', `roll-column roll-${level}`);
    const members = rows.filter((child) => child.readiness_level === level && child.valid);
    addText(section, 'h3', `${level[0].toUpperCase() + level.slice(1)} readiness · ${members.length}`);
    members.forEach((child) => addText(section, 'p', `${child.roll_no}. ${child.first_name}`));
  }
}
document.querySelector('[data-view="check-view"]').addEventListener('click', loadRoll);
$('download-roll').addEventListener('click', (event) => { event.preventDefault(); window.location.href = `/api/classes/${selectedClass().id}/roll-template.csv`; });
$('upload-roll').addEventListener('click', async () => {
  const file = $('roll-file').files[0]; if (!file) return;
  const form = new FormData(); form.append('file', file);
  try {
  const response = await getJson(`/api/classes/${selectedClass().id}/roll/upload`, {method:'POST', body:form});
  const preview = response.rows;
  state.rollPreviewRows = preview;
  state.rollPreviewInvalid = preview.some((x) => !x.valid);
  showRollPreview(preview);
  $('roll-paste-low').value = preview.filter((x) => x.readiness_level === 'low').map((x) => x.first_name).join('\n');
  $('roll-paste-mid').value = preview.filter((x) => x.readiness_level === 'mid').map((x) => x.first_name).join('\n');
  $('roll-paste-high').value = preview.filter((x) => x.readiness_level === 'high').map((x) => x.first_name).join('\n');
  const review = $('roll-review') || document.createElement('div');
  if (!review.id) {
    review.id = 'roll-review';
    review.className = 'roll-review';
    const heading = document.createElement('h3'); heading.textContent = 'Review the suggested buckets'; review.append(heading);
    const message = document.createElement('p'); message.textContent = 'Saathi has organised the uploaded names below. You can move names between buckets before saving the class roll.'; review.append(message);
    [$('roll-paste-low'), $('roll-paste-mid'), $('roll-paste-high')].forEach((field) => review.append(field));
    $('save-roll').parentElement.insertBefore(review, $('save-roll'));
  }
  review.classList.remove('hidden');
  $('save-roll').textContent = 'Save these buckets';
  if (state.rollPreviewInvalid) showRollMessage('Review needed: some rows are missing a name or have an invalid readiness level. Nothing has been saved.', 'error');
  else showRollMessage('Preview ready: please check the three buckets, then save the roll.', 'success');
  } catch (error) { showRollMessage(error.message, 'error'); }
});
$('save-roll').addEventListener('click', async () => {
  if (!$('roll-file').files[0] && ![$('roll-paste-low'), $('roll-paste-mid'), $('roll-paste-high')].some((field) => field.value.trim())) {
    showRollMessage('Choose a file and press Preview, or type names into the three boxes.', 'error'); return;
  }
  if ($('roll-file').files[0] && !state.rollPreviewRows) {
    showRollMessage('Previewing your file first…', 'success'); $('upload-roll').click(); return;
  }
  if (state.rollPreviewInvalid) { showRollMessage('Fix the flagged upload rows before saving. Nothing has been saved.', 'error'); return; }
  const names = [['low', $('roll-paste-low').value], ['mid', $('roll-paste-mid').value], ['high', $('roll-paste-high').value]];
  let roll;
  if (state.rollPreviewRows) {
    const levelsByName = new Map(); names.forEach(([level, text]) => text.split('\n').map((name) => name.trim()).filter(Boolean).forEach((name) => levelsByName.set(name, level)));
    roll = state.rollPreviewRows.filter((item) => item.valid).map((item) => ({roll_no: Number(item.roll_no), first_name: item.first_name, readiness_level: levelsByName.get(String(item.first_name).trim()) || item.readiness_level}));
  } else {
    roll = []; let number = 1;
    names.forEach(([level, text]) => text.split('\n').map((name) => name.trim()).filter(Boolean).forEach((first_name) => roll.push({roll_no:number++, first_name, readiness_level:level})));
  }
  try { await getJson(`/api/classes/${selectedClass().id}/roll/save`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(roll)}); await loadRoll(); showRollMessage(`Roll saved: ${roll.length} children organised into Low, Mid, and High readiness.`); }
  catch (error) { showRollMessage(error.message, 'error'); }
});
[$('roll-paste-low'), $('roll-paste-mid'), $('roll-paste-high')].forEach((field) => field.addEventListener('input', () => {
  if (!$('roll-file').files[0]) state.rollPreviewRows = null;
}));
