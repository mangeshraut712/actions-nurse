async function boot() {
  const health = document.getElementById('health');
  try {
    const h = await fetch('/api/health').then((r) => r.json());
    health.textContent = h.gemma_key ? 'Gemma key ready' : 'Rules mode (no GEMINI_API_KEY)';
    health.classList.add('ok');
  } catch { health.textContent = 'API offline'; }

  const box = document.getElementById('fixtures');
  const fixtures = await fetch('/api/fixtures').then((r) => r.json());
  for (const name of fixtures.fixtures) {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = name;
    b.onclick = async () => {
      const data = await fetch('/api/fixtures/' + name).then((r) => r.json());
      document.getElementById('log').value = data.log;
    };
    box.appendChild(b);
  }

  document.getElementById('triage').onclick = async () => {
    const btn = document.getElementById('triage');
    const log = document.getElementById('log').value.trim();
    const file = document.getElementById('image').files[0];
    if (!log && !file) return alert('Paste a log or attach a screenshot');
    btn.disabled = true;
    try {
      let data;
      if (file) {
        const fd = new FormData();
        fd.append('image', file);
        fd.append('log', log);
        data = await fetch('/api/triage-image', { method: 'POST', body: fd }).then((r) => r.json());
      } else {
        data = await fetch('/api/triage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ log }),
        }).then((r) => r.json());
      }
      document.getElementById('result').hidden = false;
      document.getElementById('summary').textContent = data.summary;
      document.getElementById('step').textContent = data.failing_step;
      document.getElementById('cause').textContent = data.root_cause;
      document.getElementById('fix').textContent = data.suggested_fix;
      document.getElementById('conf').textContent = data.confidence;
      document.getElementById('engine').textContent = data.engine;
    } finally { btn.disabled = false; }
  };
}
boot();
