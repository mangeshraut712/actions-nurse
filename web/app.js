/**
 * Actions Nurse — Frontend Application Logic
 * Hacktoberfest Hack Day Pune x Cloud Native Pune
 */

async function boot() {
  const healthEl = document.getElementById('health');
  const fixturesEl = document.getElementById('fixtures');
  const triageBtn = document.getElementById('triage');
  const logEl = document.getElementById('log');
  const fileInput = document.getElementById('image');
  const fileLabel = document.querySelector('.file');
  const resultPanel = document.getElementById('result');

  // 1. Health check
  try {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error('Health check failed');
    const health = await res.json();
    if (health.gemma_key) {
      healthEl.textContent = 'Gemma 4 key ready';
      healthEl.className = 'pill ok';
    } else {
      healthEl.textContent = 'Rules mode (no GEMINI_API_KEY)';
      healthEl.className = 'pill ok';
    }
  } catch (err) {
    console.error('Health check error:', err);
    healthEl.textContent = 'API offline';
    healthEl.className = 'pill offline';
  }

  // 2. Load fixtures
  try {
    const res = await fetch('/api/fixtures');
    const data = await res.json();
    const fixtures = data.fixtures || [];

    fixturesEl.innerHTML = '';
    for (const name of fixtures) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = name;
      btn.title = `Load fixture ${name}`;
      btn.onclick = async () => {
        // Toggle active styling
        fixturesEl.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');

        try {
          const fixRes = await fetch(`/api/fixtures/${encodeURIComponent(name)}`);
          const fixData = await fixRes.json();
          if (fixData.log) {
            logEl.value = fixData.log;
            logEl.focus();
          }
        } catch (err) {
          console.error(`Failed loading fixture ${name}:`, err);
        }
      };
      fixturesEl.appendChild(btn);
    }
  } catch (err) {
    console.error('Failed to load fixtures:', err);
    fixturesEl.innerHTML = '<span style="color:var(--muted);font-size:0.8rem">Failed to load fixtures</span>';
  }

  // 3. File selection indicator
  if (fileInput && fileLabel) {
    const fileStatus = document.createElement('span');
    fileStatus.className = 'file-selected';
    fileLabel.parentNode.insertBefore(fileStatus, fileLabel.nextSibling);

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files[0]) {
        fileStatus.textContent = `Attached: ${fileInput.files[0].name}`;
      } else {
        fileStatus.textContent = '';
      }
    });
  }

  // 4. Triage action
  triageBtn.addEventListener('click', async () => {
    const log = logEl.value.trim();
    const file = fileInput && fileInput.files && fileInput.files[0];

    if (!log && !file) {
      alert('Please paste a failed CI log or select a sample fixture above.');
      logEl.focus();
      return;
    }

    triageBtn.disabled = true;
    const originalText = triageBtn.textContent;
    triageBtn.textContent = 'Triaging failure...';

    try {
      let data;
      if (file) {
        // Multimodal path
        const fd = new FormData();
        fd.append('image', file);
        fd.append('log', log);
        fd.append('model', 'gemma-4-26b-a4b-it');

        const res = await fetch('/api/triage-image', {
          method: 'POST',
          body: fd,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        data = await res.json();
      } else {
        // Text path
        const res = await fetch('/api/triage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            log: log,
            model: 'gemma-4-26b-a4b-it',
          }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        data = await res.json();
      }

      // Render result
      resultPanel.hidden = false;
      document.getElementById('summary').textContent = data.summary || 'Triage completed.';
      document.getElementById('step').textContent = data.failing_step || 'Unknown';
      document.getElementById('cause').textContent = data.root_cause || 'Not identified';
      document.getElementById('fix').textContent = data.suggested_fix || 'Inspect CI logs.';

      // Confidence badge
      const confEl = document.getElementById('conf');
      const conf = (data.confidence || 'medium').toLowerCase();
      confEl.innerHTML = `<span class="badge badge-${conf}">${conf.toUpperCase()}</span>`;

      // Engine badge
      const engineEl = document.getElementById('engine');
      const engine = (data.engine || 'rules').toLowerCase();
      const engineLabel = engine === 'gemma' ? 'Gemma 4' : 'Rules';
      engineEl.innerHTML = `<span class="badge badge-${engine}">${engineLabel}</span>`;

      // Scroll result into view smoothly
      resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      console.error('Triage failed:', err);
      alert('Error triaging CI failure. Please check backend connection.');
    } finally {
      triageBtn.disabled = false;
      triageBtn.textContent = originalText;
    }
  });
}

document.addEventListener('DOMContentLoaded', boot);
