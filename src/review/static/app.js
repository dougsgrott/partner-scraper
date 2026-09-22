/* The review tool's whole frontend: three hash-routed views over the JSON API.
 * Vanilla JS on purpose — no build step, no npm (docs/review-tool-plan.md).
 *
 * Keyboard-first: j/k next/previous pending, 1–5 pick a verdict or label, f full page,
 * n notes, Enter submit-and-advance. Every submit is durable server-side, so closing
 * the tab loses nothing.
 */
'use strict';

const $view = document.getElementById('view');
const $crumb = document.getElementById('crumb');
const $progress = document.getElementById('progress');
const $keys = document.getElementById('keys');

async function api(path, opts = {}) {
  if (opts.body !== undefined) {
    opts.method = opts.method || 'POST';
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch('/api' + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

const esc = (s) => String(s ?? '').replace(/[&<>"']/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------------------------------------------------------------- router

const S = { queue: null, items: [], idx: -1, bundle: null,
            selected: null, notes: '', reveal: null, flips: null };

function route() {
  const m = location.hash.match(/^#\/queue\/(\d+)/);
  S.reveal = null; S.selected = null;
  if (m) openQueue(Number(m[1]));
  else dashboard();
}
window.addEventListener('hashchange', route);

// ---------------------------------------------------------------- dashboard

const GRADE_KEYS = [['true', '1'], ['partly', '2'], ['false', '3'], ['unverified', '4']];

async function dashboard() {
  S.queue = null;
  $crumb.textContent = '';
  $progress.textContent = '';
  $keys.textContent = '';
  $view.innerHTML = '<p class="muted">loading…</p>';
  let queues = [], acc = [], snaps = [];
  try {
    [queues, acc, snaps] = await Promise.all([
      api('/queues'), api('/accuracy').then((d) => d.rows), api('/snapshots')]);
  } catch (err) {
    $view.innerHTML = `<p class="error">${esc(err.message)}</p>`;
    return;
  }

  const cards = queues.map((q) => {
    const p = q.progress || { done: 0, total: 0 };
    const pct = p.total ? Math.round(100 * p.done / p.total) : 0;
    const pair = `#${q.params.before} → #${q.params.after}`;
    return `<div class="card">
      <div class="cardrow"><h4>${esc(q.title)}</h4><span class="chip">${esc(q.kind)}</span></div>
      <div class="muted">${pair}${q.params.prompt_version ? ' · v' + esc(q.params.prompt_version) : ''}
        · ${esc(q.params.selection || q.params.source || '')}</div>
      ${q.error ? `<div class="flag">${esc(q.error)}</div>` : ''}
      <div class="bar"><div style="width:${pct}%"></div></div>
      <div class="cardrow"><span class="muted">${p.done} / ${p.total}</span>
        <a href="#/queue/${q.id}"><button class="primary">${p.done >= p.total && p.total ? 'Open' : 'Resume'}</button></a>
      </div></div>`;
  }).join('') || '<p class="muted">no queues yet — create one below.</p>';

  const accRows = acc.map((r) => `<tr>
    <td>#${r.before}→#${r.after}</td><td>v${esc(r.prompt_version ?? '?')}</td>
    <td>${esc(r.selection ?? '?')}</td><td>${esc(r.method)}</td>
    <td>${esc(r.grader ?? '—')}</td>
    <td class="num">${r.true}</td><td class="num">${r.partly}</td>
    <td class="num">${r.false}</td><td class="num">${r.unverified}</td>
    <td class="num">${r.rate == null ? '—' : Math.round(r.rate * 100) + '%'}${r.selection === 'targeted' ? '*' : ''}</td>
    <td class="num">${r.weighted == null ? '—' : Math.round(r.weighted * 100) + '%'}</td>
  </tr>`).join('');

  const snapOpts = snaps.map((s) =>
    `#${s.id}${s.label ? ' (' + s.label + ')' : ''} — ${s.page_count} pages`).join('\n');

  $view.innerHTML = `
    <h2>Queues</h2><div class="cards">${cards}</div>
    <h2>Accuracy</h2>
    ${acc.length ? `<table><tr><th>pair</th><th>prompt</th><th>selection</th><th>method</th>
      <th>grader</th><th>true</th><th>partly</th><th>false</th><th>unver</th>
      <th>rate</th><th>weighted</th></tr>${accRows}</table>
      <p class="muted">* targeted — not a rate.</p>` : '<p class="muted">no verdicts stored yet.</p>'}
    <h2>New queue</h2>
    <form class="create" id="createform">
      <div class="row">
        <div><label>kind</label><select name="kind" id="kindsel">
          <option value="grading">grading</option><option value="labeling">labeling</option>
        </select></div>
        <div style="flex:2"><label>title</label><input name="title" required></div>
      </div>
      <div class="row">
        <div><label>before snapshot</label><input name="before" required placeholder="e.g. 6"></div>
        <div><label>after snapshot</label><input name="after" required placeholder="e.g. 7"></div>
      </div>
      <div id="gradingfields">
        <div class="row">
          <div><label>n (draw size)</label><input name="n" value="10"></div>
          <div><label>seed</label><input name="seed" value="1"></div>
          <div><label>prompt version (arm, optional)</label><input name="prompt_version"></div>
        </div>
        <div class="row">
          <div><label>grader</label><input name="grader" placeholder="doug"></div>
          <div><label>finding ids (targeted — overrides the draw)</label>
            <input name="finding_ids" placeholder="e.g. 333, 351"></div>
        </div>
      </div>
      <div id="labelingfields" style="display:none">
        <div class="row">
          <div><label>source</label><select name="source">
            <option value="absence">absence scan</option>
            <option value="stratified">stratified added lines</option></select></div>
          <div><label>n (stratified)</label><input name="n2" value="100"></div>
          <div><label>seed</label><input name="seed2" value="1"></div>
          <div><label>labeler</label><input name="labeler" placeholder="doug"></div>
        </div>
      </div>
      <label>note</label><input name="note">
      <div class="submitrow"><button class="primary" type="submit">Create</button>
        <span id="createmsg" class="muted"></span></div>
      <p class="muted">snapshots:<br><span class="mono">${esc(snapOpts)}</span></p>
    </form>`;

  document.getElementById('kindsel').onchange = (e) => {
    const grading = e.target.value === 'grading';
    document.getElementById('gradingfields').style.display = grading ? '' : 'none';
    document.getElementById('labelingfields').style.display = grading ? 'none' : '';
  };
  document.getElementById('createform').onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(e.target);
    const kind = f.get('kind');
    const params = { before: Number(f.get('before')), after: Number(f.get('after')) };
    if (kind === 'grading') {
      params.n = Number(f.get('n') || 10);
      params.seed = Number(f.get('seed') || 1);
      if (f.get('prompt_version')) params.prompt_version = f.get('prompt_version');
      if (f.get('grader')) params.grader = f.get('grader');
      const ids = (f.get('finding_ids') || '').split(/[\s,]+/).filter(Boolean).map(Number);
      if (ids.length) params.finding_ids = ids;
    } else {
      params.source = f.get('source');
      params.n = Number(f.get('n2') || 100);
      params.seed = Number(f.get('seed2') || 1);
      if (f.get('labeler')) params.labeler = f.get('labeler');
    }
    const msg = document.getElementById('createmsg');
    msg.textContent = 'creating… (first diff of a pair takes a moment)';
    try {
      const q = await api('/queues', { body: {
        kind, title: f.get('title'), note: f.get('note') || null, params } });
      location.hash = `#/queue/${q.id}`;
    } catch (err) { msg.innerHTML = `<span class="error">${esc(err.message)}</span>`; }
  };
}

// ---------------------------------------------------------------- queue

async function openQueue(id) {
  $view.innerHTML = '<p class="muted">materializing queue… (first open of a pair diffs it)</p>';
  try {
    S.queue = await api(`/queues/${id}`);
  } catch (err) {
    $view.innerHTML = `<p class="error">${esc(err.message)}</p>`;
    return;
  }
  S.items = S.queue.items;
  S.flips = S.queue.flips || null;
  const pending = S.items.findIndex((i) => !i.done);
  S.idx = pending === -1 ? 0 : pending;
  $crumb.textContent = `· ${S.queue.title} (${S.queue.kind})`;
  $keys.textContent = 'j/k next/prev pending · 1–5 verdict/label · f full page · '
    + 'n notes · Enter submit & advance';
  await loadItem();
}

function headerProgress() {
  const done = S.items.filter((i) => i.done).length;
  let text = `${done} / ${S.items.length}`;
  if (S.flips && S.flips.with_pre_label) {
    text += ` · flips ${S.flips.flips}/${S.flips.with_pre_label}`;
  }
  $progress.textContent = text;
}

async function loadItem() {
  S.reveal = null; S.selected = null; S.notes = '';
  headerProgress();
  const item = S.items[S.idx];
  if (!item) { $view.innerHTML = '<p class="muted">empty queue.</p>'; return; }
  renderShell('<p class="muted">loading evidence…</p>');
  try {
    S.bundle = await api(`/queues/${S.queue.id}/items/${item.id}`);
  } catch (err) {
    renderShell(`<p class="error">${esc(err.message)}</p>`);
    return;
  }
  renderShell(S.queue.kind === 'grading' ? renderGrading() : renderLabeling());
  wireControls();
}

function renderShell(workHtml) {
  const list = S.items.map((it, i) => {
    const label = S.queue.kind === 'grading'
      ? `<span class="chip ${esc(it.impact)}">${esc(it.impact)}</span> ${esc(it.summary)}`
      : `${esc(it.slug)}: ${esc(it.line)}`;
    return `<a href="javascript:void(0)" data-idx="${i}" class="${i === S.idx ? 'current' : ''}">
      ${it.done ? '<span class="tick">✓</span> ' : ''}${label.slice(0, 400)}</a>`;
  }).join('');
  $view.innerHTML = `<div class="queue">
    <nav class="itemlist">
      <div class="cardrow" style="padding:4px 8px">
        <button id="exportbtn" title="write the provenance file">Export</button>
        <span id="exportmsg" class="muted" style="font-size:12px"></span>
      </div>${list}</nav>
    <section class="work">${workHtml}</section></div>`;
  $view.querySelectorAll('.itemlist a').forEach((a) => {
    a.onclick = () => { S.idx = Number(a.dataset.idx); loadItem(); };
  });
  const exp = document.getElementById('exportbtn');
  if (exp) exp.onclick = async () => {
    const msg = document.getElementById('exportmsg');
    try {
      const r = await api(`/queues/${S.queue.id}/export`, { body: {} });
      msg.innerHTML = `<span class="ok">${esc(r.count)} → ${esc(r.path)}</span>`;
    } catch (err) { msg.innerHTML = `<span class="error">${esc(err.message)}</span>`; }
  };
}

function diffLineHtml(sign, text, extra = '') {
  const cls = sign.includes('~') ? 'rev' : sign.includes('-') ? 'rem' : 'add';
  return `<div class="diffline ${cls} ${extra}">${esc(sign)} ${esc(text)}</div>`;
}

// ---------------------------------------------------------------- grading view

function renderGrading() {
  const b = S.bundle, f = b.finding;
  const flags = [];
  if (b.flags.already_present.length) {
    flags.push(`claims something is new, but these already appeared in the BEFORE text `
      + `of its cited pages: ${b.flags.already_present.join(', ')}`);
  }
  if (b.flags.newness_unverifiable) {
    flags.push('claims newness or contrast with the past, but no before text exists for '
      + 'its cited pages — the check could NOT run; verify by hand');
  }
  for (const [q, other] of b.flags.misquoted_before) {
    flags.push(`quotes the old text as saying "${q}" — not found in the BEFORE text`
      + (other ? ' (it IS in the AFTER text: likely quoting the new page as the old)' : ''));
  }
  for (const [q, other] of b.flags.misquoted_after) {
    flags.push(`quotes the new text as saying "${q}" — not found in the AFTER text`
      + (other ? ' (it IS in the BEFORE text: likely quoting the old page as the new)' : ''));
  }

  const evid = b.evidence.map((ev) => `<div class="evidence">
    <div class="head"><span class="chip">${esc(ev.kind)}</span>
      <span class="slug">${esc(ev.slug)}</span>
      ${ev.note ? `<span class="muted">(${esc(ev.note)})</span>` : ''}</div>
    <div class="difflines">${ev.lines.map(([s, t]) => diffLineHtml(s, t)).join('')}</div>
    ${ev.diff ? `<details class="fulldiff"><summary>unified diff (capped)</summary>
      <pre>${ev.diff.split('\n').map((ln) =>
        /^(~?[-+])/.test(ln) && !/^(\+\+\+|---)/.test(ln)
          ? diffLineHtml(ln.match(/^(~?[-+])/)[1], ln.replace(/^~?[-+]/, ''))
          : esc(ln)).join('\n')}</pre></details>` : ''}
    <details class="fullpage" data-url="${esc(ev.url)}">
      <summary>full page — before / after (f)</summary>
      <div class="pagepair muted">fetching…</div></details>
  </div>`).join('');

  const evNote = b.cited > b.shown * 2
    ? `<div class="flag">only ${Math.round(100 * b.shown / b.cited)}% of the evidence is
       shown — the finding cites ${b.cited} pages.</div>` : '';

  const choices = GRADE_KEYS.map(([v, k]) =>
    `<button data-choice="${v}"><span class="key">${k}</span>${v}</button>`).join('');

  return `
    <p><span class="chip ${esc(f.impact)}">${esc(f.impact)}</span>
      ${f.kind ? `<span class="chip">${esc(f.kind)}</span>` : ''}
      <span class="muted">finding ${f.id} · cites ${b.cited} page(s), showing ${b.shown}
      ${f.prompt_version ? '· prompt v' + esc(f.prompt_version) : ''}</span></p>
    <h2>${esc(f.summary)}</h2>
    ${f.detail ? `<p>${esc(f.detail)}</p>` : ''}
    ${flags.map((t) => `<div class="flag">! ${esc(t)}</div>`).join('')}
    ${evNote}${evid}
    <div class="controls" id="controls">
      <div class="choices">${choices}</div>
      <textarea id="notes" placeholder="notes (n)"></textarea>
      <div class="submitrow">
        <button class="primary" id="submitbtn" disabled>Submit (Enter)</button>
        <span class="muted">method: full-page · blind — prior verdicts appear after submit</span>
      </div>
    </div>
    <div id="revealbox">${b.done && b.prior ? revealHtml(b.prior, null) : ''}</div>`;
}

function revealHtml(prior, stored) {
  const rows = prior.map((v) => `<tr>
    <td>${esc(v.verdict)}</td><td>${esc(v.method)}</td><td>${esc(v.grader ?? '—')}</td>
    <td>${esc(v.graded_at)}</td><td>${esc(v.source ?? '')}</td>
    <td>${esc(v.notes ?? '')}</td></tr>`).join('');
  return `<div class="reveal">
    <h3>${stored ? `Stored: ${esc(stored.verdict)} (${esc(stored.method)}). ` : ''}Prior verdicts — revealed</h3>
    ${prior.length ? `<table><tr><th>verdict</th><th>method</th><th>grader</th>
      <th>graded</th><th>source</th><th>notes</th></tr>${rows}</table>`
      : '<p class="muted">none — this finding had no prior grades.</p>'}
    ${stored ? '<p class="muted">Enter / j — next pending</p>' : ''}</div>`;
}

// ---------------------------------------------------------------- labeling view

function renderLabeling() {
  const b = S.bundle;
  const keyFor = (i) => String(i + 1);
  const choices = b.taxonomy.map((t, i) =>
    `<button data-choice="${esc(t)}"><span class="key">${keyFor(i)}</span>${esc(t)}</button>`)
    .join('')
    + `<button data-choice="${esc(b.skip)}"><span class="key">s</span>${esc(b.skip)} / unsure</button>`;
  const norm = (s) => s.replace(/\s+/g, ' ').trim();
  const ctx = (lines, sign) => lines.map((ln) =>
    diffLineHtml(sign, ln, sign === '+' && norm(ln) === norm(b.line) ? 'target' : ''))
    .join('') || '<div class="diffline muted">(none readable)</div>';

  return `
    <p><span class="chip">${esc(b.stratum)}</span>
      <span class="muted">${esc(b.slug)}</span></p>
    <div class="bigline">+ ${esc(b.line)}</div>
    <p>pre-label: ${b.pre_label
      ? `<span class="chip">${esc(b.pre_label)}</span> <span class="muted">by ${esc(b.pre_labeler)}</span>`
      : '<span class="muted">none</span>'}
      ${b.done ? ` · <span class="ok">labeled: ${esc(b.label)}</span>` : ''}</p>
    <div class="ctxcols">
      <div><h5>− removed (before)</h5><div class="difflines">${ctx(b.context_removed, '-')}</div></div>
      <div><h5>+ added (after)</h5><div class="difflines">${ctx(b.context_added, '+')}</div></div>
    </div>
    <details class="fullpage" data-url="${esc(b.url)}">
      <summary>full page — before / after (f)</summary>
      <div class="pagepair muted">fetching…</div></details>
    <div class="controls" id="controls">
      <div class="choices">${choices}</div>
      <textarea id="notes" placeholder="notes (n)"></textarea>
      <div class="submitrow">
        <button class="primary" id="submitbtn" disabled>Submit (Enter)</button>
        <span id="flipnote" class="muted"></span>
      </div>
    </div><div id="revealbox"></div>`;
}

// ---------------------------------------------------------------- shared wiring

function wireControls() {
  $view.querySelectorAll('[data-choice]').forEach((btn) => {
    btn.onclick = () => selectChoice(btn.dataset.choice);
  });
  const submitBtn = document.getElementById('submitbtn');
  if (submitBtn) submitBtn.onclick = submit;
  const notes = document.getElementById('notes');
  if (notes) notes.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
    if (e.key === 'Escape') notes.blur();
  });
  $view.querySelectorAll('details.fullpage').forEach((d) => {
    d.addEventListener('toggle', () => { if (d.open) fetchPage(d); }, { once: false });
  });
}

function selectChoice(choice) {
  S.selected = choice;
  $view.querySelectorAll('[data-choice]').forEach((b) =>
    b.classList.toggle('selected', b.dataset.choice === choice));
  const btn = document.getElementById('submitbtn');
  if (btn) btn.disabled = false;
}

async function fetchPage(details) {
  const box = details.querySelector('.pagepair');
  if (box.dataset.loaded) return;
  box.dataset.loaded = '1';
  try {
    const p = await api(`/queues/${S.queue.id}/page?url=${encodeURIComponent(details.dataset.url)}`);
    box.classList.remove('muted');
    box.innerHTML = `
      <div><h5>before</h5><pre>${p.before == null ? '(no stored body)' : esc(p.before)}</pre></div>
      <div><h5>after</h5><pre>${p.after == null ? '(no stored body)' : esc(p.after)}</pre></div>`;
  } catch (err) { box.innerHTML = `<span class="error">${esc(err.message)}</span>`; }
}

async function submit() {
  if (!S.selected || S.reveal) return;
  const item = S.items[S.idx];
  const notes = (document.getElementById('notes') || {}).value || '';
  const body = S.queue.kind === 'grading'
    ? { verdict: S.selected, notes }
    : { label: S.selected, notes };
  let result;
  try {
    result = await api(`/queues/${S.queue.id}/items/${item.id}`, { body });
  } catch (err) {
    document.getElementById('revealbox').innerHTML =
      `<p class="error">${esc(err.message)}</p>`;
    return;
  }
  item.done = true;
  if (S.queue.kind === 'grading') {
    item.verdict = S.selected;
    S.reveal = result;
    document.getElementById('revealbox').innerHTML =
      revealHtml(result.prior, result.stored);
    document.getElementById('revealbox').scrollIntoView({ block: 'nearest' });
  } else {
    item.label = S.selected;
    S.flips = result.flips;
    headerProgress();
    nextPending();  // labeling reveals nothing; straight on
    return;
  }
  headerProgress();
}

function nextPending() {
  const after = S.items.findIndex((it, i) => i > S.idx && !it.done);
  const anywhere = S.items.findIndex((it) => !it.done);
  const next = after !== -1 ? after : anywhere;
  if (next === -1) {
    S.idx = Math.min(S.idx + 1, S.items.length - 1);
    loadItem().then(() => {
      const box = document.getElementById('revealbox');
      if (box && S.items.every((i) => i.done)) {
        box.insertAdjacentHTML('beforeend',
          '<p class="ok">queue complete — Export writes the provenance file.</p>');
      }
    });
    return;
  }
  S.idx = next;
  loadItem();
}

function move(delta) {
  const n = S.items.length;
  if (!n) return;
  let i = S.idx;
  for (let step = 0; step < n; step++) {
    i = (i + delta + n) % n;
    if (!S.items[i].done) { S.idx = i; loadItem(); return; }
  }
  S.idx = (S.idx + delta + n) % n;  // all done: plain move
  loadItem();
}

document.addEventListener('keydown', (e) => {
  if (!S.queue) return;
  const tag = (e.target.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'select' || tag === 'textarea') return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const grading = S.queue.kind === 'grading';
  if (e.key === 'j') { S.reveal ? nextPending() : move(1); }
  else if (e.key === 'k') move(-1);
  else if (e.key === 'Enter') {
    e.preventDefault();
    if (S.reveal) nextPending(); else submit();
  } else if (e.key === 'n') {
    e.preventDefault();
    const notes = document.getElementById('notes');
    if (notes) notes.focus();
  } else if (e.key === 'f') {
    const d = $view.querySelector('details.fullpage');
    if (d) { d.open = !d.open; }
  } else if (/^[0-9]$/.test(e.key) || e.key === 's') {
    if (S.reveal) return;
    if (grading) {
      const hit = GRADE_KEYS.find(([, k]) => k === e.key);
      if (hit) selectChoice(hit[0]);
    } else if (S.bundle) {
      if (e.key === 's' || e.key === '0') selectChoice(S.bundle.skip);
      else {
        const t = S.bundle.taxonomy[Number(e.key) - 1];
        if (t) selectChoice(t);
      }
    }
  }
});

route();
