const state = { boards: [], classes: [], currentResult: null, rollPreviewInvalid: false, rollPreviewRows: null };
state.check = null;
const $ = (id) => document.getElementById(id);
async function readableError(response, fallback) { let data={}; try { data=await response.json(); } catch (_) {} const detail=data.detail; if (typeof detail === 'string') return detail; if (Array.isArray(detail)) return detail.map((item) => typeof item === 'string' ? item : (item.msg || item.message || 'Invalid value')).join('. '); return fallback; }
[['signup-username','signup-username'],['signup-password','signup-password'],['signup-confirm','signup-confirm'],['signup-email','signup-email'],['signup-consent','signup-consent'],['login-username','login-username'],['login-password','login-password'],['reset-password','reset-password'],['reset-confirm','reset-confirm'],['reset-message','reset-message']].forEach(([id, testid]) => { const node = $(id); if (node) node.dataset.testid = testid; });
const resetSubmit = document.querySelector('#reset-form button'); if (resetSubmit) resetSubmit.dataset.testid = 'reset-submit';
const signupSubmit = document.querySelector('#signup-form button'); if (signupSubmit) signupSubmit.dataset.testid = 'signup-submit';
const loginSubmit = document.querySelector('#login-form button'); if (loginSubmit) loginSubmit.dataset.testid = 'login-submit';
const forgotSubmit = document.querySelector('#forgot-form button'); if (forgotSubmit) forgotSubmit.dataset.testid = 'forgot-submit';
if ($('signup-username')) $('signup-username').setAttribute('pattern', '[-A-Za-z0-9._]{3,30}');
const forgotLink = document.createElement('button'); forgotLink.id='forgot-link'; forgotLink.type='button'; forgotLink.textContent='Forgot password?'; forgotLink.dataset.testid='forgot-link'; forgotLink.className='secondary'; document.getElementById('login-form')?.append(forgotLink);
const isMcqCheck = (check) => check.check_type === 'mcq' || check.check_type === 'mcq_read_aloud';

function addText(parent, tag, text, className = '') {
  const element = document.createElement(tag);
  element.textContent = text == null ? '' : String(text);
  if (className) element.className = className;
  parent.appendChild(element);
  return element;
}
function classroomGreeting() {
  const now = new Date(); const hour = now.getHours(); const time = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const note = ['Small steps every day add up.', 'Every child can grow.', 'Your careful noticing makes a difference.'][now.getDate() % 3];
  const greeting = document.createElement('p'); greeting.className = 'classroom-greeting'; greeting.textContent = `${time}! ☀️ ${note}`; document.querySelector('.topbar')?.append(greeting);
}
function celebrate(message = 'Ready! ⭐') { const burst = document.createElement('div'); burst.className = 'star-burst'; burst.setAttribute('aria-live', 'polite'); burst.textContent = `✦  ${message}  ✦`; document.body.append(burst); setTimeout(() => burst.remove(), 1200); }
classroomGreeting();

async function getJson(url, options) {
  options = options || {};
  options.headers = Object.assign({}, options.headers || {}, {
    'X-Saathi-Access-Code': localStorage.getItem('saathi_access_code') || ''
  });
  const response = await fetch(url, options);
  const body = await response.text();
  let data = {};
  try { data = body ? JSON.parse(body) : {}; } catch (_) { data = {detail: body}; }
  if (response.status === 401) { sessionStorage.setItem('saathi-plan-draft', JSON.stringify(Object.fromEntries(['current-situation','classroom-vision','unit-goal','chapter-input','topic-input','note-input'].map((id) => [id, $(id)?.value || ''])))); document.querySelector('#auth-screen')?.classList.remove('hidden'); showAuth('login'); const error = new Error('Please log in again'); error.sessionExpired = true; throw error; }
  if (!response.ok) throw new Error(typeof data.detail === 'string' && data.detail ? data.detail : (body || 'The request could not be completed.'));
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
  addText(parent, 'h3', isMcqCheck(result.check) ? 'Answer check' : 'Saved observation check (read-only)');
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
  $('feedback-card').classList.remove('hidden');
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
  const lessons = await getJson(`/api/lessons/recent?class_id=${encodeURIComponent(selectedClass().id)}`);
  $('lesson-select').replaceChildren();
  lessons.forEach((lesson) => { const date = new Date(lesson.created_at); const stamp = date.toLocaleDateString(undefined, {weekday:'short', day:'numeric', month:'short'}) + ', ' + date.toLocaleTimeString(undefined, {hour:'2-digit', minute:'2-digit'}); const topic = lesson.topic || lesson.chapter_or_topic; $('lesson-select').add(new Option(`${stamp} · ${lesson.lesson_type || 'lesson'} · ${topic}`, lesson.check_id)); });
  const nextPicker = $('next-check-select'); if (nextPicker) { nextPicker.replaceChildren(); lessons.forEach((lesson) => { const date = new Date(lesson.created_at); const stamp = date.toLocaleDateString(undefined, {weekday:'short', day:'numeric', month:'short'}) + ', ' + date.toLocaleTimeString(undefined, {hour:'2-digit', minute:'2-digit'}); nextPicker.add(new Option(`${stamp} · ${lesson.lesson_type || 'lesson'} · ${lesson.topic || lesson.chapter_or_topic}`, lesson.check_id)); }); if (state.check) nextPicker.value = state.check.id; }
  if (lessons.length) await loadCheck(lessons[0].check_id);
}

async function loadCheck(checkId) {
  if (!checkId) return;
  state.check = await getJson(`/api/checks/${checkId}`);
  const editor = $('check-editor'); editor.replaceChildren();
  const items = state.check.items.questions || state.check.items.tasks || [];
  if (isMcqCheck(state.check)) {
    const print = addText(editor, 'button', 'Print answer sheet', 'secondary');
    print.onclick = () => { const popup = window.open('', 'saathi-answer-sheet'); if (!popup) return; popup.document.write('<!doctype html><title>Saathi answer sheet</title><style>body{font:20px sans-serif;padding:24px} .q{margin:24px 0} .o{display:inline-block;border:2px solid #111;padding:12px 20px;margin:8px}</style><h1>Roll number: __________________</h1>'); items.forEach((item, index) => { popup.document.write(`<div class="q"><strong>${index + 1}. ${item.stem}</strong><br>${Object.entries(item.options || {}).map(([key, value]) => `<span class="o">${key}. ${value}</span>`).join('')}</div>`); }); popup.document.write('</body></html>'); popup.document.close(); popup.print(); };
  }
  state.check.itemsList = items;
  state.check.values = {};
  const header = addText(editor, 'div', '', 'response-header');
  addText(header, 'strong', 'Child / roll');
  items.forEach((_, index) => addText(header, 'strong', isMcqCheck(state.check) ? `Q${index + 1}` : `T${index + 1}`));
  state.check.students.forEach((student) => {
    const row = addText(editor, 'div', '', 'response-row');
    const identity = addText(row, 'div', '', 'child-identity');
    addText(identity, 'strong', `${student.roll_no}. ${student.first_name || ''}`);
    const absent = document.createElement('input');
    absent.type = 'checkbox'; absent.title = 'Absent'; absent.className = 'absent-toggle';
    absent.onchange = () => {
      row.classList.toggle('row-absent', absent.checked);
      Object.values(state.check.values).filter((entry) => entry.roll === student.roll_no).forEach((entry) => {
        entry.button.dataset.value = absent.checked ? 'absent' : (isMcqCheck(state.check) ? 'A' : 'got_it');
        entry.button.textContent = absent.checked ? '—' : (isMcqCheck(state.check) ? 'A' : '✓');
      });
    };
    identity.appendChild(absent);
    items.forEach((item, index) => {
      const button = addText(row, 'button', isMcqCheck(state.check) ? 'A' : '✓', 'response-cell');
      button.dataset.value = isMcqCheck(state.check) ? 'A' : 'got_it';
      button.onclick = () => cycleResponse(button, state.check.check_type);
      button.roll = student.roll_no; button.itemIndex = index;
      state.check.values[`${student.roll_no}-${index}`] = {button, roll: student.roll_no, item, index};
      if (state.check.check_type === 'observation') addErrorPicker(row, button, item);
    });
  });
  if ($('sample-results')) $('sample-results').classList.toggle('hidden', !state.demoMode);
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
  const values = type === 'mcq_read_aloud' ? ['A', 'B', 'C'] : (type === 'mcq' ? ['A', 'B', 'C', 'D'] : ['got_it', 'partly', 'not_yet']);
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
    if (isMcqCheck(state.check)) response.chosen_option = button.dataset.value;
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
    const labels = isMcqCheck(state.check) ? Object.keys(item.options || {'A':'','B':'','C':'','D':''}) : ['got_it', 'partly', 'not_yet'];
    labels.forEach((label) => { const wrapper = addText(card, 'label', label); const input = document.createElement('input'); input.type = 'number'; input.min = 0; input.value = 0; input.dataset.label = label; wrapper.appendChild(input); inputs[label] = input; });
    state.check.countInputs.push(inputs);
  });
}

function collectClassCounts() {
  return Object.fromEntries(state.check.countInputs.map((inputs, index) => [index, Object.fromEntries(Object.entries(inputs).map(([label, input]) => [label, Number(input.value) || 0]))]));
}

async function load() {
  if (location.pathname === '/reset') { $('app-main').classList.add('hidden'); document.querySelector('.topbar').classList.add('hidden'); $('auth-screen').classList.add('hidden'); $('forgot-screen').classList.add('hidden'); $('reset-screen').classList.remove('hidden'); return; }
  const health = await getJson('/api/health');
  state.demoMode = health.demo_mode;
  if (health.demo_mode) $('demo-login').classList.remove('hidden');
  let me;
  try { me = await getJson('/api/auth/me'); } catch (error) { $('app-main').classList.add('hidden'); document.querySelector('.topbar').classList.add('hidden'); document.querySelector('.tabs').classList.add('hidden'); $('account-button').classList.add('hidden'); $('auth-screen').classList.remove('hidden'); showAuth('login'); return; }
  $('auth-screen').classList.add('hidden'); $('app-main').classList.remove('hidden'); document.querySelector('.topbar').classList.remove('hidden'); document.querySelector('.tabs').classList.remove('hidden');
  $('account-button').textContent = me.username.toLowerCase() === 'demo' ? 'demo account' : me.username; $('account-button').classList.remove('hidden'); $('account-email').textContent = me.email; $('account-name').value = me.display_name || ''; $('account-school').value = me.school || '';
  const [boards, classes] = await Promise.all([getJson('/api/boards'), getJson('/api/classes')]);
  state.boards = boards.boards; state.classes = classes; state.demoMode = health.demo_mode; const usageTab = document.querySelector('[data-view="usage-view"]'); if (usageTab) usageTab.classList.toggle('hidden', !state.demoMode); renderClasses();
  $('key-status').classList.toggle('ready', health.key_found); $('key-status').title = health.key_found ? 'Portkey key ready' : health.message;
  await loadContext();
  const draft = sessionStorage.getItem('saathi-plan-draft'); if (draft) { Object.entries(JSON.parse(draft)).forEach(([id,value]) => { if ($(id)) $(id).value=value; }); sessionStorage.removeItem('saathi-plan-draft'); }
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
$('account-button').onclick = () => $('account-dialog').showModal();
function showSetupWizard() { $('app-main').classList.add('hidden'); document.querySelector('.tabs').classList.add('hidden'); $('setup-wizard').classList.remove('hidden'); let step=0; const labels=['First, add your first class.','Next, upload or enter your class roll.','Finally, prepare your first Plan.']; $('setup-action').onclick=()=>{ if(step<2){step++; $('setup-step').textContent=labels[step];} else finishSetup(); }; $('setup-skip').onclick=finishSetup; function finishSetup(){fetch('/api/auth/setup-complete',{method:'POST'}); $('setup-wizard').classList.add('hidden'); $('app-main').classList.remove('hidden'); document.querySelector('.tabs').classList.remove('hidden');} }
$('save-profile').onclick = async () => { const r = await fetch('/api/auth/profile', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:$('account-name').value,school:$('account-school').value})}); $('account-message').textContent = r.ok ? 'Profile saved.' : 'Could not save profile.'; };
$('change-password').onclick = async () => { const r = await fetch('/api/auth/change-password', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:$('current-password').value,new_password:$('new-password').value})}); $('account-message').textContent = r.ok ? 'Password changed.' : await readableError(r,'Could not change password.'); };
$('logout-button').onclick = async () => { await fetch('/api/auth/logout',{method:'POST'}); location.reload(); };
$('reset-form').onsubmit = async (event) => { event.preventDefault(); const token = new URLSearchParams(location.search).get('token') || ''; if ($('reset-password').value !== $('reset-confirm').value) { $('reset-message').textContent = 'Passwords do not match.'; return; } const response = await fetch('/api/auth/reset-password', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token,new_password:$('reset-password').value})}); if (!response.ok) { $('reset-message').textContent = response.status === 400 ? 'This link has expired. Request a new one.' : 'Could not reset the password.'; return; } $('reset-message').textContent = 'Password reset. You can now log in.'; };
function showAuth(form) { $('login-form').classList.toggle('hidden', form !== 'login'); $('signup-form').classList.toggle('hidden', form !== 'signup'); }
$('show-login').onclick = () => showAuth('login'); $('show-signup').onclick = () => showAuth('signup');
$('demo-login').onclick = async () => { const response = await fetch('/api/auth/login', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'demo',password:'saathi-demo'})}); if (response.ok) { await load(); } else { const data=await response.json(); $('login-error').textContent=data.detail || 'Could not log in.'; $('login-error').classList.remove('hidden'); } };
$('login-form').onsubmit = async (event) => { event.preventDefault(); const response = await fetch('/api/auth/login', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:$('login-username').value,password:$('login-password').value})}); if (!response.ok) { $('login-error').textContent=await readableError(response,'Could not log in.'); $('login-error').classList.remove('hidden'); return; } $('login-error').textContent=''; $('login-error').classList.add('hidden'); await load(); };
$('forgot-link').onclick = () => { $('auth-screen').classList.add('hidden'); $('forgot-screen').classList.remove('hidden'); };
$('forgot-back').onclick = () => { $('forgot-screen').classList.add('hidden'); $('auth-screen').classList.remove('hidden'); showAuth('login'); };
$('forgot-form').onsubmit = async (event) => { event.preventDefault(); const response=await fetch('/api/auth/forgot-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({identity:$('forgot-identity').value})}); if (response.ok) { const data=await response.json(); $('forgot-message').textContent=`${data.message}. (Local mode: the reset link is in the server log)`; } else $('forgot-message').textContent=await readableError(response,'Please try again.'); $('forgot-message').classList.remove('hidden'); };
$('signup-form').addEventListener('submit', (event) => { const username=$('signup-username').value.trim(); const password=$('signup-password').value; const confirm=$('signup-confirm').value; const email=$('signup-email').value.trim(); let message=''; if (!username) message='Username is required'; else if (!/^[A-Za-z0-9._-]{3,30}$/.test(username)) message='Username can only use letters, numbers, . _ -'; else if (password.length < 8) message='Password must be at least 8 characters'; else if (password !== confirm) message="Passwords don't match"; else if (!email) message='Email is required'; else if (!$('signup-consent').checked) message='Please tick the consent box'; if (message) { event.preventDefault(); event.stopImmediatePropagation(); $('signup-error').textContent=message; $('signup-error').classList.remove('hidden'); } }, true);
$('signup-form').onsubmit = async (event) => { event.preventDefault(); if ($('signup-password').value !== $('signup-confirm').value) { $('signup-error').textContent = "Passwords don't match"; $('signup-error').classList.remove('hidden'); return; } const response = await fetch('/api/auth/signup', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:$('signup-username').value,password:$('signup-password').value,email:$('signup-email').value,invite_code:$('signup-invite').value})}); if (!response.ok) { $('signup-error').textContent = await readableError(response, 'Could not create account. Please try again.'); $('signup-error').classList.remove('hidden'); return; } $('signup-error').textContent=''; $('signup-error').classList.add('hidden'); await load(); };
const signupButton = document.querySelector('#signup-form button'); if (signupButton) { signupButton.type='button'; signupButton.dataset.testid='signup-submit'; signupButton.onclick=() => $('signup-form').dispatchEvent(new Event('submit', {bubbles:true,cancelable:true})); }
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
$('feedback-card').addEventListener('submit', async (event) => { event.preventDefault(); const r = await fetch('/api/feedback', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({rating:Number($('feedback-rating').value),teach_decision:$('feedback-decision').value,usual_time:$('feedback-usual').value,saathi_minutes:Number($('feedback-minutes').value)||null,comment:$('feedback-comment').value,teacher_name:$('feedback-name').value})}); $('feedback-message').textContent = r.ok ? 'Thank you — your feedback was saved.' : 'Please check the feedback fields.'; });
$('add-class-button').onclick = () => $('class-dialog').showModal(); $('close-dialog').onclick = () => $('class-dialog').close();
$('class-form').addEventListener('submit', async (event) => { event.preventDefault(); const resources = [...document.querySelectorAll('#class-form input[type=checkbox]:checked')].map((item) => item.value); const created = await getJson('/api/classes', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({board:$('new-board').value, grade:Number($('new-grade').value), section:$('new-section').value, class_size:Number($('new-size').value), period_minutes:Number($('new-period').value), resources})}); state.classes = await getJson('/api/classes'); renderClasses(); $('class-select').value = created.id; refreshSubjects(); $('class-dialog').close(); });
document.querySelectorAll('.tabs button').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('.tabs button').forEach((item) => item.classList.remove('active')); button.classList.add('active'); document.querySelectorAll('.view').forEach((view) => view.classList.add('hidden')); $(button.dataset.view).classList.remove('hidden'); if (button.dataset.view === 'usage-view') loadUsage(); }));
load();
$('lesson-select').addEventListener('change', (event) => loadCheck(event.target.value));
async function renderQuickAnalysis() {
  const insight = await getJson(`/api/checks/${state.check.id}/insight`);
  const panel = $('check-step-analysis'); if (!panel) return;
  panel.replaceChildren(); addText(panel, 'h2', '④ Class analysis'); addText(panel, 'p', 'Confirmed results from the selected lesson.');
  const bars = addText(panel, 'div', '', 'analysis-metrics');
  insight.concepts.forEach((concept) => { const metric = addText(bars, 'div', '', 'analysis-metric'); addText(metric, 'strong', concept.concept_id); addText(metric, 'span', `${concept.percent_correct}% · ${concept.status}`); });
  const next = addText(panel, 'button', 'See what to do next →', 'primary'); next.onclick = () => document.querySelector('[data-view="next-view"]').click();
}
$('save-results').addEventListener('click', async () => { if (!state.check) return; const payload = state.check.mode === 'class_count' ? {check_mode:'class_count', class_counts:collectClassCounts()} : {check_mode:'each_child', responses:collectResponses()}; await getJson(`/api/checks/${state.check.id}/responses`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); await renderQuickAnalysis(); alert('Results confirmed. The analysis is ready.'); });
$('sample-results').addEventListener('click', fillSampleResults);
$('each-child-mode').addEventListener('click', () => { state.check.mode = 'each_child'; loadCheck(state.check.id); });
$('class-count-mode').addEventListener('click', () => { state.check.mode = 'class_count'; renderClassCounts(); });
document.querySelector('[data-view="check-view"]').addEventListener('click', loadLessons);
document.querySelector('[data-view="next-view"]').addEventListener('click', async () => { const current = selectedClass(); if (!current) return; const lessons = await getJson(`/api/lessons/recent?class_id=${encodeURIComponent(current.id)}`); const picker = $('next-check-select'); picker.replaceChildren(); lessons.forEach((lesson) => { const date = new Date(lesson.created_at); const stamp = date.toLocaleDateString(undefined, {weekday:'short', day:'numeric', month:'short'}) + ', ' + date.toLocaleTimeString(undefined, {hour:'2-digit', minute:'2-digit'}); picker.add(new Option(`${stamp} · ${lesson.lesson_type || 'lesson'} · ${lesson.topic || lesson.chapter_or_topic}`, lesson.check_id)); }); if (state.check) picker.value = state.check.id; const checkId = picker.value || state.check?.id; if (!checkId) { $('next-summary').textContent = 'Confirm results in the Check tab first.'; return; } const result = await getJson(`/api/checks/${checkId}/next-steps`, {method:'POST'}); const content = $('next-content'); content.replaceChildren(); addText(content, 'h3', 'Class insight'); result.insight.concepts.forEach((concept) => addText(content, 'p', `${concept.concept_id}: ${concept.percent_correct}% · ${concept.status}`)); addText(content, 'h3', 'Top errors'); result.insight.top_errors.slice(0, 3).forEach((error) => addText(content, 'p', `${error.count} children: ${error.description}${error.ai_suggested ? ' (AI-suggested)' : ''}`)); addText(content, 'h3', 'Coach summary'); addText(content, 'p', result.next_steps.summary); addText(content, 'h3', 'Next lesson warm-up'); addText(content, 'p', result.next_steps.next_lesson_warmup); const warmup = addText(content, 'button', 'Use in next lesson', 'primary'); warmup.onclick = async () => { await getJson(`/api/checks/${checkId}/use-warmup`, {method:'POST'}); warmup.textContent = 'Added to next lesson ✓'; warmup.disabled = true; }; const history = await getJson(`/api/progress/${current.id}`); const progress = $('progress-history'); progress.replaceChildren(); Object.entries(history.concepts).forEach(([concept, checks]) => { const row = addText(progress, 'p', `${concept}: `); checks.forEach((item) => addText(row, 'span', `${item.percent}%`, `progress-${item.status.replaceAll(' ', '-').toLowerCase()}`)); }); });
if (!document.getElementById('progress-history')) { const history = document.createElement('div'); history.id = 'progress-history'; history.className = 'hidden'; $('next-content').append(history); }
$('next-tab-button').addEventListener('click', () => { $('next-tab-content').classList.remove('hidden'); $('resources-tab-content').classList.add('hidden'); });
$('resources-tab-button').addEventListener('click', () => { $('next-tab-content').classList.add('hidden'); $('resources-tab-content').classList.remove('hidden'); });
function downloadText(filename, content) { const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([content], {type:'text/plain;charset=utf-8'})); link.download = filename; link.textContent = `Download ${filename}`; link.className = 'secondary resource-download'; $('resource-content').append(link); setTimeout(() => URL.revokeObjectURL(link.href), 60000); }
function renderResources(result, heading) { const target = $('resource-content'); target.replaceChildren(); addText(target, 'h3', `${heading} · ${result.resources.resources.length}`); const text = result.resources.resources.map((item) => [item.title, item.level && `Readiness: ${item.level}`, ...(item.items || []), ...(item.answers || []), ...(item.strengths || []), ...(item.home_activities || []), item.parent_guidance, item.hard_now, item.opening_script].filter(Boolean).join('\n')).join('\n\n'); result.resources.resources.forEach((item) => { const card = addText(target, 'article', '', 'resource-card'); addText(card, 'h4', item.title); if (item.level) addText(card, 'p', `Readiness: ${item.level}`); [['Items', item.items], ['Answers', item.answers], ['Strengths', item.strengths], ['Home activities', item.home_activities]].forEach(([label, values]) => { if (values?.length) { addText(card, 'strong', label); values.forEach((value) => addText(card, 'p', value)); } }); [['Parent guidance', item.parent_guidance], ['Current difficulty', item.hard_now], ['Opening script', item.opening_script]].forEach(([label, value]) => { if (value) { addText(card, 'strong', label); addText(card, 'p', value); } }); }); downloadText(`${heading.toLowerCase().replaceAll(' ', '-')}.txt`, text); }
$('generate-worksheets').addEventListener('click', async () => { if (!state.check) { $('resource-content').textContent = 'Confirm results in Check first.'; return; } try { renderResources(await getJson(`/api/checks/${state.check.id}/resources/worksheets`, {method:'POST'}), 'Worksheets'); } catch (error) { $('resource-content').textContent = error.message; } });
$('generate-meetings').addEventListener('click', async () => { if (!state.check) { $('resource-content').textContent = 'Confirm results in Check first.'; return; } try { renderResources(await getJson(`/api/checks/${state.check.id}/resources/meeting_plans`, {method:'POST'}), 'Parent–teacher meeting plans'); } catch (error) { $('resource-content').textContent = error.message; } });
$('generate-leader-onepager').addEventListener('click', async () => { if (!state.check) { $('resource-content').textContent = 'Confirm results in Check first.'; return; } try { const insight = await getJson(`/api/checks/${state.check.id}/insight`); const target = $('resource-content'); target.replaceChildren(); addText(target, 'h3', 'One-pager for school leader'); const text = [`${insight.top_errors.length} recorded error patterns from the confirmed class results.`, ...insight.top_errors.map((error) => `${error.count} children: ${error.description}`)].join('\n'); addText(target, 'p', text); downloadText('school-leader-one-pager.txt', text); } catch (error) { $('resource-content').textContent = error.message; } });

// The roll editor deliberately uses textContent for names and imported values.
async function loadRoll() {
  const roll = await getJson(`/api/classes/${selectedClass().id}/roll`);
  const columns = $('roll-columns'); columns.replaceChildren();
  for (const level of ['low', 'mid', 'high']) {
    const section = addText(columns, 'section', '', `roll-column roll-${level}`);
    const members = roll.filter((child) => child.readiness_level === level);
    addText(section, 'h3', `${level[0].toUpperCase() + level.slice(1)} · ${members.length}`);
    members.forEach((child) => addText(section, 'p', `${child.roll_no}. ${child.first_name || 'Unnamed'}`));
  }
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
function renderReviewGrid(parent, review) {
  const card = addText(parent, 'section', '', 'review-grid-card'); addText(card, 'h3', 'Review answers before confirming');
  const table = document.createElement('table'); const head = table.insertRow(); ['Roll', 'Question', 'Read', 'Mark', 'Confidence'].forEach((label) => addText(head.insertCell(), 'strong', label));
  review.cells.forEach((cell) => { const row = table.insertRow(); addText(row.insertCell(), 'span', cell.roll_no); addText(row.insertCell(), 'span', `Q${cell.question_number}`); const answer = document.createElement('select'); ['A','B','C','D','unreadable'].forEach((option) => answer.add(new Option(option, option))); answer.value = cell.answer || 'unreadable'; row.insertCell().append(answer); const mark = addText(row.insertCell(), 'span', cell.mark === 1 ? '✓' : cell.mark === 0 ? '✗' : '?'); const confidence = addText(row.insertCell(), 'span', cell.confidence); if (cell.confidence !== 'high' || cell.unreadable) row.className = 'low-confidence'; answer.onchange = () => { cell.answer = answer.value; cell.mark = answer.value === review.questions[cell.question_number - 1].correct_option ? 1 : 0; mark.textContent = cell.mark ? '✓' : '✗'; cell.edited = true; }; });
  card.append(table); addText(card, 'p', 'Low-confidence and unreadable cells are highlighted. Tap a cell to correct what was read.'); const confirm = addText(card, 'button', 'Confirm results', 'primary'); confirm.onclick = async () => { const payload = review.cells.map((cell) => ({roll_no: cell.roll_no, question_number: cell.question_number, answer: cell.answer, mark: cell.mark, max_marks: 1, edited: Boolean(cell.edited)})); await getJson(`/api/papers/${review.paper_id}/results/confirm`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); confirm.textContent = 'Results confirmed ✓'; confirm.disabled = true; };
}
function renderClassAnalysis(analysis, progress) {
  const metrics = analysis.querySelector('.analysis-metrics');
  metrics.replaceChildren();
  [['Class average', progress.class_average == null ? '—' : `${progress.class_average}%`], ['Student-wise mastery', `${progress.checked} students checked`], ['Question-wise mastery', `${(progress.questions || []).length} questions analysed`]].forEach(([label, value]) => { const metric = document.createElement('div'); metric.className = 'analysis-metric'; addText(metric, 'strong', label); addText(metric, 'span', value); metrics.append(metric); });
  addText(analysis, 'p', 'Analysis updated automatically from the uploaded answer sheets.', 'success');
}
function buildSimpleCheckFlow() {
  const view = $('check-view');
  if (document.getElementById('check-step-submissions')) return;
  const title = document.createElement('div'); title.className = 'hero';
  addText(title, 'p', 'Check learning', 'eyebrow'); addText(title, 'h2', 'Understand what your class knows.');
  addText(title, 'p', 'Upload the class roll and student work. Saathi will organise the evidence and show class, student, and question mastery.'); view.append(title);

  const existingCards = view.querySelectorAll(':scope > .card');
  if (existingCards[1]) existingCards[1].remove();
  const roll = document.querySelector('#check-view > .card');
  if (roll) { const heading = roll.querySelector('h2'); if (heading) heading.textContent = '① Class roll'; }
  const rollInput = document.createElement('input'); rollInput.type = 'file'; rollInput.accept = '.pdf,.csv,.xlsx,.xlsm,application/pdf,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'; rollInput.id = 'simple-roll-file'; roll.append(rollInput);
  const rollSave = addText(roll, 'button', 'Save roll', 'primary'); rollSave.type = 'button';
  roll.querySelector('.roll-actions')?.remove(); roll.querySelectorAll('#roll-paste-low, #roll-paste-mid, #roll-paste-high, #save-roll')?.forEach((node) => node.remove());
  const rollStatus = addText(roll, 'p', 'No class roll uploaded.', 'upload-status'); rollInput.addEventListener('change', () => { rollStatus.textContent = rollInput.files[0] ? `Ready: ${rollInput.files[0].name}` : 'No class roll uploaded.'; });
  rollInput.addEventListener('change', async () => {
    if (!rollInput.files[0]) return;
    const form = new FormData(); form.append('file', rollInput.files[0]);
    try {
      const endpoint = /\.pdf$/i.test(rollInput.files[0].name) ? 'upload-pdf' : 'upload';
      const parsed = await getJson(`/api/classes/${selectedClass().id}/roll/${endpoint}`, {method:'POST', body:form});
      state.rollPreviewRows = parsed.rows; state.rollPreviewInvalid = false; showRollPreview(parsed.rows);
      const byLevel = Object.fromEntries(['low', 'mid', 'high'].map((level) => [level, parsed.rows.filter((row) => row.readiness_level === level).map((row) => row.first_name).join('\n')]));
      $('roll-paste-low').value = byLevel.low; $('roll-paste-mid').value = byLevel.mid; $('roll-paste-high').value = byLevel.high;
      rollStatus.textContent = 'Roll preview ready. Review the buckets, then save the roll.';
    } catch (error) { rollStatus.textContent = error.message; }
  });
  rollSave.addEventListener('click', async () => {
    if (!state.rollPreviewRows || state.rollPreviewInvalid) { rollStatus.textContent = 'Preview a valid PDF, CSV, or Excel file first.'; return; }
    try { const roll = state.rollPreviewRows.filter((row) => row.valid).map((row) => ({roll_no: Number(row.roll_no), first_name: row.first_name, readiness_level: row.readiness_level})); await getJson(`/api/classes/${selectedClass().id}/roll/save`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(roll)}); await loadRoll(); rollStatus.textContent = `Roll saved: ${roll.length} children.`; }
    catch (error) { rollStatus.textContent = error.message; }
  });
  if (!roll) view.append(roll);

  const lessonCard = document.createElement('section'); lessonCard.id = 'check-step-lesson'; lessonCard.className = 'card check-flow-card';
  addText(lessonCard, 'h2', '② Choose the lesson'); addText(lessonCard, 'p', 'The selected lesson’s check is the answer key.');
  const lessonSelect = document.createElement('select'); lessonSelect.id = 'lesson-select'; lessonCard.append(lessonSelect);
  const keyPreview = document.createElement('div'); keyPreview.id = 'check-editor'; keyPreview.className = 'hidden'; lessonCard.append(keyPreview);
  const print = addText(lessonCard, 'button', 'Print answer sheet', 'secondary'); print.type = 'button'; print.onclick = () => window.print();
  view.append(lessonCard); loadLessons().catch((error) => addText(lessonCard, 'p', error.message, 'roll-message error'));

  const submissions = document.createElement('section'); submissions.id = 'check-step-submissions'; submissions.className = 'card check-flow-card';
  addText(submissions, 'h2', '② Upload submissions');
  addText(submissions, 'p', 'Upload one PDF containing all students’ completed answer sheets. Results and class analysis update automatically.');
  const choices = document.createElement('div'); choices.className = 'submission-choices'; submissions.append(choices);
  const uploadArea = document.createElement('div'); uploadArea.className = 'submission-upload hidden'; submissions.append(uploadArea);
  const cards = [['all-students', 'All students in one file', 'Upload a PDF containing completed answer sheets. Each sheet should show the child’s name and roll number from the class roll.', 'Upload the document or import from Google Drive', 'single']];
  cards.forEach(([id, heading, description, direction, mode]) => {
    const card = document.createElement('button'); card.type = 'button'; card.className = 'submission-card'; card.dataset.mode = mode;
    addText(card, 'strong', heading); addText(card, 'span', description); card.addEventListener('click', () => {
      choices.querySelectorAll('.submission-card').forEach((item) => item.classList.remove('selected')); card.classList.add('selected'); uploadArea.replaceChildren(); uploadArea.classList.remove('hidden');
      addText(uploadArea, 'strong', direction);
      const drop = addText(uploadArea, 'label', 'Drag and drop student files here, or click to browse', 'drop-zone');
      const input = document.createElement('input'); input.type = 'file'; input.accept = '.pdf,.png,.jpg,.jpeg,.heic,.doc,.docx,.ppt,.pptx,application/pdf,image/*'; input.multiple = mode === 'multiple'; drop.append(input);
      input.addEventListener('change', async () => { if (!state.check || !input.files.length) return; const form = new FormData(); [...input.files].forEach((file) => form.append('files', file)); try { const uploaded = await getJson(`/api/checks/${state.check.id}/submissions`, {method:'POST', body:form}); state.lastPaperId = uploaded.paper_id; const read = await getJson(`/api/papers/${uploaded.paper_id}/read-submissions`, {method:'POST'}); const review = await getJson(`/api/papers/${uploaded.paper_id}/review-grid`); const payload = review.cells.map((cell) => ({roll_no: cell.roll_no, question_number: cell.question_number, answer: cell.answer, mark: cell.mark, max_marks: 1, edited: false})); await getJson(`/api/papers/${uploaded.paper_id}/results/confirm`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); const progress = await getJson(`/api/papers/${uploaded.paper_id}/progress`); renderClassAnalysis(document.getElementById('check-step-analysis'), progress); addText(uploadArea, 'p', 'Answer sheets read. Class analysis updated.', 'success'); } catch (error) { addText(uploadArea, 'p', error.message, 'roll-message error'); } });
      const note = addText(uploadArea, 'small', mode === 'multiple' ? 'PDF, image, Word, and PowerPoint files are supported.' : 'PDF, image, Word, and PowerPoint files are supported.');
      input.addEventListener('change', () => { note.textContent = input.files.length ? `${input.files.length} file${input.files.length === 1 ? '' : 's'} selected.` : 'No files selected.'; });
      if (mode === 'single') { const drive = addText(uploadArea, 'button', 'Import from Google Drive', 'secondary'); drive.type = 'button'; drive.disabled = true; drive.title = 'Google Drive import will be connected in a later step.'; }
    }); choices.append(card);
  }); view.append(submissions);

  const analysis = document.createElement('section'); analysis.id = 'check-step-analysis'; analysis.className = 'card check-flow-card';
  addText(analysis, 'h2', '③ Class analysis'); addText(analysis, 'p', 'After the answer-sheet PDF is uploaded, results are read and analysed automatically.');
  const metrics = document.createElement('div'); metrics.className = 'analysis-metrics';
  [['Class average', '—'], ['Student-wise mastery', 'Upload submissions to calculate'], ['Question-wise mastery', 'Upload submissions to calculate']].forEach(([label, value]) => { const metric = document.createElement('div'); metric.className = 'analysis-metric'; addText(metric, 'strong', label); addText(metric, 'span', value); metrics.append(metric); });
  analysis.append(metrics); const next = addText(analysis, 'button', 'See what to do next →', 'primary'); next.type = 'button'; next.addEventListener('click', () => document.querySelector('[data-view="next-view"]').click()); view.append(analysis);
}
function labelCheckSteps() {
  const cards = document.querySelectorAll('#check-view > .card');
  if (cards[0]) { cards[0].querySelector('h2').textContent = '① Class roll'; }
  if (cards[1]) {
    cards[1].querySelector('h2').textContent = '④ Class progress / quick check';
    if (!document.getElementById('check-step-guide')) {
      const guide = document.createElement('div'); guide.id = 'check-step-guide'; guide.className = 'card check-step-guide';
      guide.innerHTML = '<h2>② Question paper</h2><p>Use a Saathi lesson check here. Upload-and-confirm question papers and answer-sheet reading are not connected to this screen yet.</p><h2>③ Choose children and answer sheets</h2><p>The quick tap grid is available below. Selection, paper upload, answer-sheet upload, review, and confirmation still need to be wired into the Check flow.</p>';
      cards[1].before(guide);
    }
  }
  const quick = document.getElementById('check-editor');
  if (quick && !document.getElementById('quick-entry-link')) { const link = document.createElement('p'); link.id = 'quick-entry-link'; link.textContent = 'No answer sheets? Enter results quickly'; quick.before(link); }
}
document.querySelector('[data-view="check-view"]').addEventListener('click', buildSimpleCheckFlow);
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
