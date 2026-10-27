/**
 * Actions Nurse — Frontend
 * Open Agent Hackathon 2026 Wildcard [Tinkerer]
 */

function evidenceText(value, limit = 360) {
  const raw = typeof value === 'string' ? value : value == null ? '' : String(value);
  // The API is designed not to return credentials, but never put token-like
  // text into the demo UI if a backend or upstream payload changes.
  const redacted = raw
    .replace(/\b(?:authorization\s*[:=]\s*)?bearer\s+\S+/gi, '[redacted]')
    .replace(/\b(?:api[_-]?key|password|token)\s*[:=]\s*\S+/gi, '[redacted]')
    .replace(/\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/g, '[redacted]');
  return redacted.length > limit ? `${redacted.slice(0, limit - 1)}…` : redacted;
}

function renderZetarisEvidence(zetaris) {
  const evidenceEl = document.getElementById('zetarisEvidence');
  const detailsEl = document.getElementById('zetarisEvidenceDetails');
  detailsEl.replaceChildren();

  const result = zetaris?.result || {};
  const rowCount = result.row_count;
  const mode = zetaris?.mode;
  const source = evidenceText(zetaris?.source, 80);
  const provenance = evidenceText(zetaris?.provenance, 80);
  const isLive = mode === 'live';
  const isFixture = mode === 'fixture';
  const sourceLabel = isLive
    ? source === 'zetaris-local-session'
      ? 'live local read-only query'
      : 'live read-only query'
    : isFixture
      ? 'recorded reference fixture'
      : mode === 'unavailable'
        ? 'unavailable'
        : `status: ${evidenceText(mode, 80)}`;
  const provenanceLabel = isFixture
    ? 'synthetic reference data'
    : isLive
      ? provenance === 'synthetic-local-demo'
        ? 'synthetic local demo rows'
        : provenance
          ? `${provenance} provenance`
          : 'provenance not classified'
      : 'no evidence returned';

  evidenceEl.textContent = mode
    ? `Zetaris ${sourceLabel} · ${provenanceLabel}${rowCount !== undefined ? ` · ${rowCount} matching row${rowCount === 1 ? '' : 's'}` : ''}${result.fixture ? ` · ${evidenceText(result.fixture, 120)}` : ''}.`
    : 'Zetaris evidence was not requested for this result.';

  if (!mode) return;

  const expectedStep = evidenceText(zetaris?.failing_step, 200);
  const rows = Array.isArray(result.data) ? result.data : [];
  const relevantRows = isLive
    ? rows.filter((row) => row && typeof row === 'object' && evidenceText(row.failing_step, 200) === expectedStep).slice(0, 3)
    : [];

  if (relevantRows.length) {
    const list = document.createElement('ol');
    list.className = 'zetaris-evidence-list';
    relevantRows.forEach((row) => {
      const item = document.createElement('li');
      const signature = document.createElement('strong');
      signature.textContent = evidenceText(row.failure_signature, 240) || 'Recorded CI signature';
      const recommendation = document.createElement('p');
      recommendation.textContent = evidenceText(row.latest_recommendation, 360) || 'No recommendation recorded.';
      const provenanceLine = document.createElement('small');
      const occurrences = evidenceText(row.occurrences, 24);
      const rowSource = evidenceText(row.source, 120);
      provenanceLine.textContent = `${occurrences ? `${occurrences} prior occurrence${occurrences === '1' ? '' : 's'} · ` : ''}${rowSource || provenanceLabel}`;
      item.append(signature, recommendation, provenanceLine);
      list.appendChild(item);
    });
    detailsEl.appendChild(list);
  } else if (isLive && rowCount) {
    const note = document.createElement('small');
    note.className = 'zetaris-evidence-note';
    note.textContent = 'Matching rows were returned, but none matched the diagnosed failing step closely enough to display as corroboration.';
    detailsEl.appendChild(note);
  }

  if (result.request_id) {
    const request = document.createElement('small');
    request.className = 'zetaris-evidence-note';
    request.textContent = `Request ID: ${evidenceText(result.request_id, 96)}`;
    detailsEl.appendChild(request);
  }

  if (result.sql) {
    const sqlDetails = document.createElement('details');
    sqlDetails.className = 'zetaris-sql';
    const summary = document.createElement('summary');
    summary.textContent = 'Read-only SQL used for this evidence';
    const sql = document.createElement('code');
    sql.textContent = evidenceText(result.sql, 1200);
    sqlDetails.append(summary, sql);
    detailsEl.appendChild(sqlDetails);
  }
}

function renderResult(data) {
  const resultPanel = document.getElementById('result');
  resultPanel.hidden = false;
  document.getElementById('summary').textContent = data.summary || 'Triage completed.';
  document.getElementById('step').textContent = data.failing_step || 'Unknown';
  document.getElementById('cause').textContent = data.root_cause || 'Not identified';
  document.getElementById('fix').textContent = data.suggested_fix || 'Inspect CI logs.';
  const cmds = data.fix_commands || [];
  const commandsEl = document.getElementById('cmds');
  commandsEl.replaceChildren();
  if (!cmds.length) {
    commandsEl.textContent = '—';
  } else {
    const list = document.createElement('div');
    list.className = 'command-list';
    cmds.forEach((command) => {
      const row = document.createElement('div');
      row.className = 'command';
      const code = document.createElement('code');
      code.textContent = command;
      const copy = document.createElement('button');
      copy.type = 'button';
      copy.className = 'copy-command';
      copy.textContent = 'Copy';
      copy.onclick = async () => {
        try {
          await navigator.clipboard.writeText(command);
          copy.textContent = 'Copied';
          setTimeout(() => { copy.textContent = 'Copy'; }, 1200);
        } catch (_) {}
      };
      row.append(code, copy);
      list.appendChild(row);
    });
    commandsEl.appendChild(list);
  }
  const confEl = document.getElementById('conf');
  const conf = (data.confidence || 'medium').toLowerCase();
  confEl.innerHTML = `<span class="badge badge-${conf}">${conf.toUpperCase()}</span>`;
  const engine = (data.engine || 'rules').toLowerCase();
  document.getElementById('engine').innerHTML =
    `<span class="badge badge-${engine}">${engine === 'gemma' ? 'Gemma 4' : 'Rules'}</span>`;
  const validation = document.getElementById('validation');
  const validationStatus = data.validation_status || 'not_run';
  validation.textContent = data.validation_detail || (validationStatus === 'not_run'
    ? 'No Gemma proposal returned; deterministic Rules result shown.'
    : validationStatus);
  validation.className = `validation-copy validation-${validationStatus}`;

  const memory = data.memory || {};
  const recall = Array.isArray(memory.recall) ? memory.recall : [];
  const memoryEl = document.getElementById('memoryRecall');
  if (memory.engine_source) {
    const memoryNames = recall.map((item) => item.content).filter(Boolean).slice(0, 2);
    memoryEl.textContent = memoryNames.length
      ? `${memory.recall_service || 'H-MEM recall'} from ${memory.engine_source}: ${memoryNames.join(' · ')}`
      : `${memory.mode || 'H-MEM'} is ready via ${memory.engine_source}; no similar recall cleared the threshold.`;
  } else {
    memoryEl.textContent = `H-MEM ${memory.mode || 'setup'}: ${memory.reason || 'run the documented setup to enable durable recall.'}`;
  }

  renderZetarisEvidence(data.zetaris || {});

  const activity = data.activity || {};
  const activityEl = document.getElementById('activityTrace');
  activityEl.textContent = activity.id
    ? `${activity.id} · ${activity.path || 'demo/activity/trace.jsonl'}`
    : 'Activity logging is unavailable for this request.';
  resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function boot() {
  const healthEl = document.getElementById('health');
  const runtimeHint = document.getElementById('runtimeHint');
  const fixturesEl = document.getElementById('fixtures');
  const triageBtn = document.getElementById('triage');
  const compareBtn = document.getElementById('compare');
  const clearBtn = document.getElementById('clear');
  const logEl = document.getElementById('log');
  const fileInput = document.getElementById('image');
  const fileLabel = document.querySelector('.file');
  let fileStatus = null;
  const screenshotDemoBtn = document.getElementById('loadScreenshotDemo');
  const demoStatus = document.getElementById('demoStatus');
  const preview = document.getElementById('imagePreview');
  const previewImage = document.getElementById('previewImage');
  const previewCaption = document.getElementById('previewCaption');
  let runtimeHealth = null;
  let previewUrl = null;

  function setStatus(message) {
    demoStatus.textContent = message;
  }

  function clearResults() {
    document.getElementById('result').hidden = true;
    document.getElementById('comparePanel').hidden = true;
  }

  function showImage(file, caption) {
    if (!file) {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrl = null;
      preview.hidden = true;
      previewImage.removeAttribute('src');
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);
    previewImage.src = previewUrl;
    previewCaption.textContent = caption || `Attached: ${file.name}`;
    preview.hidden = false;
  }

  clearBtn.addEventListener('click', () => {
    logEl.value = '';
    if (fileInput) fileInput.value = '';
    clearResults();
    document.querySelector('.file-selected')?.replaceChildren();
    showImage(null);
    setStatus('Ready for another failure. Choose a fixture, paste a log, or load the bundled red screenshot.');
    fixturesEl.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
    logEl.focus();
  });

  try {
    const res = await fetch('/api/health');
    const health = await res.json();
    runtimeHealth = health;
    healthEl.textContent = health.rules_only ? 'Rules-only demo' : (health.gemma_key ? `Gemma-first · ${health.gemma_budget_seconds}s fallback` : 'Rules ready · no key');
    healthEl.className = 'pill ok';
    if (health.rules_only) {
      runtimeHint.textContent = 'Rules-only mode is active. No Gemma request is made; deterministic rules diagnose from the log. Commands are suggestions only — review before running.';
    } else if (!health.gemma_key) {
      runtimeHint.textContent = 'No Gemini API key is configured. Rules diagnose logs; add a key to try Gemma 4, then rules check known failure categories. Commands are suggestions only — review before running.';
    } else {
      runtimeHint.textContent = 'Gemma 4 proposes first within a 20-second budget. Deterministic rules check known failure categories and override conflicts. Commands are suggestions only — review before running.';
    }
  } catch (err) {
    healthEl.textContent = 'API offline';
    healthEl.className = 'pill offline';
  }

  try {
    const res = await fetch('/api/fixtures');
    const data = await res.json();
    fixturesEl.innerHTML = '';
    for (const name of data.fixtures || []) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = name.replace(/\.txt$/, '');
      btn.onclick = async () => {
        fixturesEl.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        const fixRes = await fetch(`/api/fixtures/${encodeURIComponent(name)}`);
        const fixData = await fixRes.json();
        if (fixData.log) logEl.value = fixData.log;
        if (fileInput) fileInput.value = '';
        if (fileStatus) fileStatus.textContent = '';
        showImage(null);
        clearResults();
        setStatus(`Loaded ${name.replace(/\.txt$/, '')}. Press “Triage with Gemma 4” to diagnose it.`);
      };
      fixturesEl.appendChild(btn);
    }
  } catch (_) {
    fixturesEl.innerHTML = '<span style="color:var(--muted);font-size:0.8rem">Failed to load fixtures</span>';
  }

  if (fileInput && fileLabel) {
    fileStatus = document.createElement('span');
    fileStatus.className = 'file-selected';
    fileLabel.parentNode.insertBefore(fileStatus, fileLabel.nextSibling);
    fileInput.addEventListener('change', () => {
      const file = fileInput.files?.[0];
      fileStatus.textContent = file ? `Attached: ${file.name}` : '';
      showImage(file);
      clearResults();
      if (file) setStatus('Screenshot attached. Add a log for stronger evidence, then triage with Gemma 4.');
    });
  }

  screenshotDemoBtn?.addEventListener('click', async () => {
    screenshotDemoBtn.disabled = true;
    screenshotDemoBtn.textContent = 'Preparing demo…';
    clearResults();
    try {
      const [imageRes, logRes] = await Promise.all([
        fetch('/demo-assets/red-actions-permission-failure.png'),
        fetch('/api/fixtures/checkout-auth.txt'),
      ]);
      if (!imageRes.ok || !logRes.ok) throw new Error('demo asset missing');
      const blob = await imageRes.blob();
      const file = new File([blob], 'red-actions-permission-failure.png', { type: 'image/png' });
      const transfer = new DataTransfer();
      transfer.items.add(file);
      fileInput.files = transfer.files;
      fileStatus.textContent = 'Attached: red-actions-permission-failure.png';
      const fixture = await logRes.json();
      logEl.value = fixture.log || '';
      showImage(file, 'Bundled red Actions screenshot — checkout permission failure');
      setStatus('Screenshot + checkout-auth fixture loaded. Running the multimodal comparison…');
      fixturesEl.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
      await runCompare({ auto: true });
    } catch (_) {
      setStatus('Could not load the bundled screenshot demo. You can still attach any CI screenshot.');
    } finally {
      screenshotDemoBtn.disabled = false;
      screenshotDemoBtn.textContent = 'Run screenshot demo · 1 click';
    }
  });

  const fixEl = document.getElementById('fix');
  if (fixEl) {
    fixEl.style.cursor = 'pointer';
    fixEl.title = 'Click to copy suggested fix';
    fixEl.addEventListener('click', async () => {
      const text = fixEl.textContent;
      if (!text?.trim()) return;
      try {
        await navigator.clipboard.writeText(text.trim());
        const orig = fixEl.textContent;
        fixEl.textContent = '✓ Copied fix to clipboard!';
        setTimeout(() => { fixEl.textContent = orig; }, 1400);
      } catch (_) {}
    });
  }

  triageBtn.addEventListener('click', async () => {
    const log = logEl.value.trim();
    const file = fileInput?.files?.[0];
    if (!log && !file) {
      alert('Please paste a failed CI log or select a sample fixture above.');
      return;
    }
    triageBtn.disabled = true;
    const originalText = triageBtn.textContent;
    triageBtn.textContent = 'Triaging failure...';
    const evidenceLabel = file ? 'log + screenshot' : 'CI log';
    if (runtimeHealth?.rules_only) {
      setStatus(`Rules-only runtime: diagnosing the ${evidenceLabel}; no model request will be made.`);
    } else if (!runtimeHealth?.gemma_key) {
      setStatus(`No Gemini API key is configured. The rules fallback will diagnose the ${evidenceLabel}.`);
    } else {
      setStatus(`Trying Gemma 4 with the ${evidenceLabel}; rules fallback is available within 20 seconds.`);
    }
    clearResults();
    try {
      let data;
      if (file) {
        const fd = new FormData();
        fd.append('image', file);
        fd.append('log', log);
        fd.append('model', 'gemma-4-26b-a4b-it');
        const res = await fetch('/api/triage-image', { method: 'POST', body: fd });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        data = await res.json();
      } else {
        const res = await fetch('/api/triage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ log, model: 'gemma-4-26b-a4b-it' }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        data = await res.json();
      }
      renderResult(data);
      const resultStatus = data.validation_status === 'overridden'
        ? 'Rules overruled a conflicting Gemma category and selected the deterministic diagnosis.'
        : data.engine === 'gemma'
          ? data.validation_status === 'confirmed'
            ? 'Gemma returned a diagnosis whose failure category matched a known Rules signature.'
            : 'Gemma returned an unverified proposal; no known Rules signature matched.'
          : 'Rules returned the deterministic diagnosis; no Gemma proposal was used.';
      setStatus(`${resultStatus} Review commands before running them.`);
    } catch (err) {
      console.error(err);
      alert('Error triaging CI failure. Please check backend connection.');
    } finally {
      triageBtn.disabled = false;
      triageBtn.textContent = originalText;
    }
  });

  compareBtn.addEventListener('click', () => runCompare());

  async function runCompare({ auto = false } = {}) {
    const log = logEl.value.trim();
    if (!log) {
      if (auto) setStatus('The screenshot loaded, but its checkout-auth log was empty.');
      else alert('Paste a log or pick a fixture first.');
      return;
    }
    compareBtn.disabled = true;
    const original = compareBtn.textContent;
    compareBtn.textContent = 'Comparing...';
    const file = fileInput?.files?.[0];
    if (runtimeHealth?.rules_only) {
      setStatus('Rules-only runtime: showing the deterministic baseline. No model request will be made.');
    } else if (!runtimeHealth?.gemma_key) {
      setStatus('No Gemini API key is configured. Showing the rules baseline; Gemma is skipped.');
    } else {
      setStatus(`Building a comparison from the CI log${file ? ' and attached screenshot' : ''}…`);
    }
    clearResults();
    try {
      let res;
      if (file) {
        const fd = new FormData();
        fd.append('log', log);
        fd.append('image', file);
        fd.append('model', 'gemma-4-26b-a4b-it');
        res = await fetch('/api/compare-image', { method: 'POST', body: fd });
      } else {
        res = await fetch('/api/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ log, model: 'gemma-4-26b-a4b-it' }),
        });
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const panel = document.getElementById('comparePanel');
      panel.hidden = false;
      document.getElementById('result').hidden = true;
      document.getElementById('rulesSummary').textContent = data.rules?.summary || '';
      document.getElementById('rulesStep').textContent = data.rules?.failing_step || '';
      document.getElementById('rulesCause').textContent = data.rules?.root_cause || '';
      document.getElementById('rulesFix').textContent = data.rules?.suggested_fix || '';
      const g = data.gemma;
      const gemmaUnavailable = runtimeHealth?.rules_only
        ? 'Rules-only mode is enabled, so Gemma was skipped. The deterministic baseline is shown.'
        : !runtimeHealth?.gemma_key
          ? 'No Gemini API key is configured, so Gemma was skipped. The deterministic baseline is shown.'
          : 'Gemma did not return a result. Check model availability, network, and the 20-second budget; rules still work.';
      document.getElementById('gemmaSummary').textContent = g?.summary || gemmaUnavailable;
      document.getElementById('gemmaStep').textContent = g?.failing_step || '—';
      document.getElementById('gemmaCause').textContent = g?.root_cause || '—';
      document.getElementById('gemmaFix').textContent = g?.suggested_fix || '—';
      const validationBanner = document.getElementById('validationBanner');
      const validationStatus = g?.validation_status || 'not_run';
      validationBanner.className = `validation-banner validation-${validationStatus}`;
      validationBanner.textContent = g
        ? g.validation_detail || 'Gemma returned a proposal; inspect it beside the deterministic baseline.'
        : 'No Gemma proposal was returned, so the deterministic baseline is the available diagnosis.';
      const skipReason = runtimeHealth?.rules_only
        ? 'rules-only mode is enabled'
        : !runtimeHealth?.gemma_key
          ? 'no Gemini API key is configured'
          : 'Gemma returned no result within the request budget';
      document.getElementById('compareHeadline').textContent = g
        ? validationStatus === 'confirmed'
          ? 'Gemma’s category matches a known failure.'
          : validationStatus === 'overridden'
            ? 'Category conflict. Rules choose the result.'
            : 'No signature matched. Gemma stays unverified.'
        : 'Rules diagnose the log when Gemma is skipped.';
      document.getElementById('compareEyebrow').textContent = g
        ? 'Evidence → proposal → category check'
        : 'Evidence → Rules baseline → diagnosis';
      document.getElementById('compareContext').textContent = g
        ? `Rules read the log. Gemma saw ${file ? 'that log plus the screenshot' : 'the same log'}; known signatures check its failure category.`
        : `Rules diagnosed the log. Gemma was skipped because ${skipReason}; this result has no model proposal.`;
      document.getElementById('flowRulesNote').textContent = data.rules?.patterns?.length
        ? 'Known log signature'
        : 'No known signature';
      document.getElementById('flowGemmaTitle').textContent = g ? 'Gemma proposal' : 'Gemma skipped';
      document.getElementById('flowGemmaNote').textContent = g
        ? `${file ? 'Log + screenshot' : 'Log only'}${g.model ? ` · ${g.model}` : ''}`
        : skipReason;
      document.getElementById('flowCheckTitle').textContent = g ? 'Category check' : 'Rules result';
      document.getElementById('flowCheckNote').textContent = g
        ? validationStatus === 'confirmed'
          ? 'Known category matched'
          : validationStatus === 'overridden'
            ? 'Conflict → Rules wins'
            : 'No known match · unverified'
        : 'Deterministic baseline';
      document.getElementById('gemmaInput').textContent = g
        ? `Gemma received ${file ? 'log + screenshot' : 'log only'}${g.model ? ` · ${g.model}` : ''}`
        : runtimeHealth?.rules_only
          ? 'Skipped · rules-only mode'
          : !runtimeHealth?.gemma_key
            ? 'Skipped · no API key'
            : 'No Gemma response returned';
      setStatus(g
        ? `Comparison ready: Rules checked the log signature; Gemma received ${file ? 'the log and screenshot' : 'the log only'}.`
        : runtimeHealth?.rules_only
          ? 'Rules baseline ready. The runtime is forced to rules-only mode, so no Gemma request was made.'
          : !runtimeHealth?.gemma_key
            ? 'Rules baseline ready. No Gemini API key is configured, so no Gemma request was made.'
            : 'Rules baseline ready. Gemma returned no result; check model availability, network, and the 20-second budget.');
      panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      console.error(err);
      if (auto) setStatus('The screenshot fixture loaded, but comparison failed. You can retry with Compare Rules vs Gemma.');
      else alert('Compare failed.');
    } finally {
      compareBtn.disabled = false;
      compareBtn.textContent = original;
    }
  }
}

document.addEventListener('DOMContentLoaded', boot);
