/* AgriTriage — Frontend Logic */

// ── Tab switching ────────────────────────────────────────────────────────────
function showTab(tab, el) {
  const triageTab = document.getElementById('triageTab');
  const quizTab   = document.getElementById('quizTab');

  if (tab === 'triage') {
    triageTab.classList.remove('hidden');
    quizTab.classList.add('hidden');
  } else {
    triageTab.classList.add('hidden');
    quizTab.classList.remove('hidden');
  }

  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  if (el) el.classList.add('active');
}

// ── Sample buttons ──────────────────────────────────────────────────────────
document.querySelectorAll('.sample-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('messageInput').value = btn.dataset.msg;
    document.getElementById('messageInput').focus();
  });
});

// ── State helpers ───────────────────────────────────────────────────────────
function showOnly(id) {
  ['idleState','loadingState','resultsContent','errorState'].forEach(s => {
    document.getElementById(s).classList.toggle('hidden', s !== id);
  });
}

function resetUI() { showOnly('idleState'); }

// ── Loading step animator ────────────────────────────────────────────────────
let stepInterval = null;

function startLoadingAnimation() {
  showOnly('loadingState');
  const steps = ['step1','step2','step3','step4'];
  let i = 0;
  steps.forEach(s => {
    const el = document.getElementById(s);
    el.classList.remove('active','done');
  });
  document.getElementById(steps[0]).classList.add('active');

  stepInterval = setInterval(() => {
    document.getElementById(steps[i]).classList.remove('active');
    document.getElementById(steps[i]).classList.add('done');
    i++;
    if (i < steps.length) {
      document.getElementById(steps[i]).classList.add('active');
    } else {
      clearInterval(stepInterval);
    }
  }, 900);
}

function stopLoadingAnimation() {
  if (stepInterval) clearInterval(stepInterval);
}

// ── Urgency ring animator ────────────────────────────────────────────────────
function animateRing(score) {
  const circumference = 150.8;
  const offset = circumference - (score / 10) * circumference;
  const ring = document.getElementById('ringFill');
  const num  = document.getElementById('scoreNum');

  ring.style.strokeDashoffset = circumference;
  num.textContent = '0';

  setTimeout(() => {
    ring.style.strokeDashoffset = offset;
    let current = 0;
    const inc = setInterval(() => {
      current++;
      num.textContent = current;
      if (current >= score) clearInterval(inc);
    }, 80);
  }, 100);
}

// ── Render results ───────────────────────────────────────────────────────────
function renderResults(data) {
  stopLoadingAnimation();

  const banner = document.getElementById('urgencyBanner');
  banner.className = 'urgency-banner urgency-' + data.urgency.toLowerCase();
  document.getElementById('urgencyLevel').textContent = data.urgency;
  document.getElementById('intentValue').textContent  = data.intent;
  animateRing(data.urgency_score);

  document.getElementById('summaryText').textContent = data.summary;

  const eg = document.getElementById('entitiesGrid');
  eg.innerHTML = '';

  const entities = data.entities;
  const simpleFields = [
    { key: 'FARMER ID',  val: entities.farmer_id || '—', hi: !!entities.farmer_id },
    { key: 'CROP TYPE',  val: entities.crop_type  || '—', hi: !!entities.crop_type  },
    { key: 'LOCATION',   val: entities.location   || '—', hi: !!entities.location   },
  ];
  simpleFields.forEach(f => {
    eg.innerHTML += `
      <div class="entity-card">
        <div class="entity-key">${f.key}</div>
        <div class="entity-val ${f.hi ? 'highlight' : ''}">${f.val}</div>
      </div>`;
  });

  const datesHTML = entities.dates.length
    ? entities.dates.map(d => `<span class="entity-tag">${d}</span>`).join('')
    : '<span style="color:var(--text-mute);font-size:12px">—</span>';
  eg.innerHTML += `
    <div class="entity-card">
      <div class="entity-key">DATES</div>
      <div class="entity-val">${datesHTML}</div>
    </div>`;

  const kwHTML = entities.issue_keywords.length
    ? entities.issue_keywords.map(k => `<span class="entity-tag">${k}</span>`).join('')
    : '<span style="color:var(--text-mute);font-size:12px">—</span>';
  eg.innerHTML += `
    <div class="entity-card" style="grid-column: span 2;">
      <div class="entity-key">ISSUE KEYWORDS</div>
      <div class="entity-val">${kwHTML}</div>
    </div>`;

  document.getElementById('draftText').textContent = data.draft_response;
  document.getElementById('metaTime').textContent = `⏱ ${data.processing_time_ms}ms`;

  showOnly('resultsContent');
}

// ── Main triage function ─────────────────────────────────────────────────────
async function runTriage() {
  const message     = document.getElementById('messageInput').value.trim();
  const senderName  = document.getElementById('senderName').value.trim();
  const senderEmail = document.getElementById('senderEmail').value.trim();
  const endpoint    = document.getElementById('apiEndpoint').value.trim();

  if (!message) {
    document.getElementById('messageInput').focus();
    document.getElementById('messageInput').style.borderColor = 'var(--red)';
    setTimeout(() => document.getElementById('messageInput').style.borderColor = '', 1500);
    return;
  }

  const btn = document.getElementById('triageBtn');
  btn.disabled = true;
  startLoadingAnimation();

  try {
    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, sender_name: senderName, sender_email: senderEmail }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || 'Server error');
    }

    const data = await resp.json();
    renderResults(data);

  } catch (err) {
    stopLoadingAnimation();
    document.getElementById('errorTitle').textContent = 'Agent Error';
    document.getElementById('errorMsg').textContent   = err.message || 'Could not connect to the backend. Make sure the server is running.';
    showOnly('errorState');
  } finally {
    btn.disabled = false;
  }
}

// ── Copy draft ───────────────────────────────────────────────────────────────
function copyDraft() {
  const text = document.getElementById('draftText').textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.querySelector('.draft-actions .action-btn');
    const orig = btn.textContent;
    btn.textContent = '✓ Copied';
    setTimeout(() => btn.textContent = orig, 1500);
  });
}

// ── Send draft ────────────────────────────────────────────────────────────────
function sendDraft() {
  const email = document.getElementById('senderEmail').value.trim();
  if (email) {
    const body = encodeURIComponent(document.getElementById('draftText').textContent);
    const sub  = encodeURIComponent('Re: Your Agriculture Support Request');
    window.open(`mailto:${email}?subject=${sub}&body=${body}`);
  } else {
    alert('Please enter sender email to send the draft.');
  }
}

// ── Enter key shortcut ───────────────────────────────────────────────────────
document.getElementById('messageInput').addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') runTriage();
});
