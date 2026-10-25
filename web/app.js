/**
 * Actions Nurse — Frontend
 * Hacktoberfest Hack Day Pune x Cloud Native Pune
 */

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
    healthEl.textContent = health.rules_only ? 'Rules-only demo' : (health.gemma_key ? 'Gemma-first · 12s fallback' : 'Rules ready · no key');
    healthEl.className = 'pill ok';
    if (health.rules_only) {
      runtimeHint.textContent = 'Rules-only mode is active. Diagnoses use deterministic rules. Commands are suggestions only — review before running.';
    } else if (!health.gemma_key) {
      runtimeHint.textContent = 'No Gemini API key is configured. Rules still diagnose logs; add a key to try Gemma 4 with a 12-second budget. Commands are suggestions only — review before running.';
    } else {
      runtimeHint.textContent = 'Gemma 4 is attempted first with a 12-second budget. Deterministic rules are the reliable fallback. Commands are suggestions only — review before running.';
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
    screenshotDemoBtn.textContent = 'Loading screenshot…';
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
      setStatus('Loaded the multimodal demo: screenshot + checkout-auth log. Press “Triage with Gemma 4”.');
      fixturesEl.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
    } catch (_) {
      setStatus('Could not load the bundled screenshot demo. You can still attach any CI screenshot.');
    } finally {
      screenshotDemoBtn.disabled = false;
      screenshotDemoBtn.textContent = 'Load red screenshot demo';
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
      setStatus(`Trying Gemma 4 with the ${evidenceLabel}; rules fallback is available within 12 seconds.`);
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
      setStatus(`${data.engine === 'gemma' ? 'Gemma 4 returned a diagnosis.' : 'Rules fallback returned a diagnosis.'} Review commands before running them.`);
    } catch (err) {
      console.error(err);
      alert('Error triaging CI failure. Please check backend connection.');
    } finally {
      triageBtn.disabled = false;
      triageBtn.textContent = originalText;
    }
  });

  compareBtn.addEventListener('click', async () => {
    const log = logEl.value.trim();
    if (!log) {
      alert('Paste a log or pick a fixture first.');
      return;
    }
    compareBtn.disabled = true;
    const original = compareBtn.textContent;
    compareBtn.textContent = 'Comparing...';
    const file = fileInput?.files?.[0];
    if (runtimeHealth?.rules_only) {
      setStatus('Rules-only runtime: returning the offline baseline. No Gemma request will be made.');
    } else if (!runtimeHealth?.gemma_key) {
      setStatus('No Gemini API key is configured. Showing the rules baseline and an empty Gemma result.');
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
          : 'Gemma did not return a result. Check model availability, network, and the 12-second budget; rules still work.';
      document.getElementById('gemmaSummary').textContent = g?.summary || gemmaUnavailable;
      document.getElementById('gemmaStep').textContent = g?.failing_step || '—';
      document.getElementById('gemmaCause').textContent = g?.root_cause || '—';
      document.getElementById('gemmaFix').textContent = g?.suggested_fix || '—';
      document.getElementById('gemmaInput').textContent = g
        ? `Gemma received ${file ? 'log + screenshot' : 'log only'}${g.model ? ` · ${g.model}` : ''}`
        : runtimeHealth?.rules_only
          ? 'Skipped · rules-only mode'
          : !runtimeHealth?.gemma_key
            ? 'Skipped · no API key'
            : 'No Gemma response returned';
      setStatus(g
        ? `Comparison ready: rules used the log; Gemma received ${file ? 'the log and screenshot' : 'the log only'}.`
        : runtimeHealth?.rules_only
          ? 'Rules baseline ready. The runtime is forced to rules-only mode, so no Gemma request was made.'
          : !runtimeHealth?.gemma_key
            ? 'Rules baseline ready. No Gemini API key is configured, so no Gemma request was made.'
            : 'Rules baseline ready. Gemma returned no result; check model availability, network, and the 12-second budget.');
      panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      console.error(err);
      alert('Compare failed.');
    } finally {
      compareBtn.disabled = false;
      compareBtn.textContent = original;
    }
  });
}

document.addEventListener('DOMContentLoaded', boot);
