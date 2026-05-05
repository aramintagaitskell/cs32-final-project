// Inject Chart.js at runtime so it doesn't block initial page load
const chartScript = document.createElement('script');
chartScript.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
document.head.appendChild(chartScript);

// Keep a reference so the old chart can be destroyed before a new one is drawn
let splitChart = null;

// Tab switching: deactivate all, then activate the clicked tab and fetch its data
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');

    if (btn.dataset.tab === 'history') loadHistory();
    if (btn.dataset.tab === 'analytics') loadAnalytics();
  });
});

async function loadDashboard() {
  try {
    const res = await fetch('/api/dashboard');
    const d = await res.json();

    setText('stat-total-dist', d.total_distance_m.toLocaleString());
    setText('stat-total-workouts', d.total_workouts);
    setText('stat-monthly-dist', d.monthly_distance_m?.toLocaleString() ?? '0');
    setText('stat-monthly-count', d.monthly_workouts ?? 0);
    // Consistency score is displayed in seconds; null means too few workouts
    setText('stat-consistency', d.consistency !== null ? d.consistency + 's' : '—');
    setText('progress-message', d.progress_message ?? '');

    if (d.best_split) {
      setText('stat-best-split', d.best_split.split_fmt);
      setText('stat-best-date', d.best_split.date);
    }

    if (d.predict_2k?.available) {
      setText('stat-2k-time', d.predict_2k.predicted_time_fmt);
      setText('stat-2k-split', d.predict_2k.predicted_split_fmt);
      setText('stat-2k-rate', d.predict_2k.avg_stroke_rate);
    } else {
      setText('stat-2k-time', '—');
      setText('stat-2k-split', 'Need more data');
      setText('stat-2k-rate', '');
    }

    renderChart(d.split_trend);
    renderDistBars(d.distance_by_type);
  } catch (e) {
    console.error('Dashboard load failed', e);
  }
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function renderChart(trend) {
  const canvas = document.getElementById('split-chart');
  const empty = document.getElementById('chart-empty');

  // Show placeholder when there's nothing to plot
  if (!trend || trend.length === 0) {
    canvas.style.display = 'none';
    empty.style.display = 'flex';
    return;
  }

  canvas.style.display = 'block';
  empty.style.display = 'none';

  // Chart.js may still be loading; poll until it's available before rendering
  const tryRender = () => {
    if (typeof Chart === 'undefined') { setTimeout(tryRender, 100); return; }

    const labels = trend.map(w => w.date.slice(5)); // "MM-DD" labels on x-axis
    const splits = trend.map(w => w.split_sec);
    const fmts   = trend.map(w => w.split_fmt);
    const types  = trend.map(w => w.type);

    // Color each point by workout type so type patterns are visible at a glance
    const colors = types.map(t => {
      if (t === 'interval')   return '#c8ff00';
      if (t === 'test_piece') return '#ffcb47';
      if (t === 'steady_state') return '#00d4ff';
      return '#6b7180';
    });

    if (splitChart) splitChart.destroy();

    splitChart = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Avg Split (sec)',
          data: splits,
          borderColor: '#00d4ff',
          backgroundColor: 'rgba(0,212,255,0.06)',
          pointBackgroundColor: colors,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.35,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              // Show formatted split and type instead of raw seconds in the tooltip
              label: ctx => `${fmts[ctx.dataIndex]}/500m · ${types[ctx.dataIndex]}`,
            },
            backgroundColor: '#14161b',
            borderColor: '#1e2128',
            borderWidth: 1,
            titleColor: '#e8e9ed',
            bodyColor: '#6b7180',
          },
        },
        scales: {
          x: {
            ticks: { color: '#6b7180', font: { family: 'DM Mono', size: 10 } },
            grid: { color: '#1e2128' },
          },
          y: {
            reverse: true, // Invert axis so faster (lower) splits appear higher
            ticks: {
              color: '#6b7180',
              font: { family: 'DM Mono', size: 10 },
              // Convert raw seconds back to m:ss for human-readable y-axis labels
              callback: val => {
                const m = Math.floor(val / 60);
                const s = Math.round(val % 60);
                return `${m}:${String(s).padStart(2,'0')}`;
              },
            },
            grid: { color: '#1e2128' },
          },
        },
      },
    });
  };

  tryRender();
}

const TYPE_COLORS = {
  steady_state:   '#00d4ff',
  interval:       '#c8ff00',
  test_piece:     '#ffcb47',
  cross_training: '#6b7180',
};

function renderDistBars(distByType) {
  const container = document.getElementById('dist-bars');
  if (!distByType || Object.keys(distByType).length === 0) {
    container.innerHTML = '<p style="color:var(--dim);font-family:var(--font-mono);font-size:.8rem">No data yet.</p>';
    return;
  }
  // Scale each bar relative to the highest-distance type (max = 100% width)
  const max = Math.max(...Object.values(distByType));
  container.innerHTML = Object.entries(distByType).map(([type, dist]) => `
    <div class="dist-row">
      <div class="dist-meta">
        <span>${type.replace('_', ' ')}</span>
        <span>${dist.toLocaleString()}m</span>
      </div>
      <div class="dist-track">
        <div class="dist-fill" style="width:${(dist/max*100).toFixed(1)}%;background:${TYPE_COLORS[type] ?? '#6b7180'}"></div>
      </div>
    </div>
  `).join('');
}

async function loadHistory() {
  const container = document.getElementById('workout-list');
  container.innerHTML = '<p class="empty-state">Loading…</p>';

  try {
    const res = await fetch('/api/workouts');
    const workouts = await res.json();

    if (!workouts.length) {
      container.innerHTML = '<p class="empty-state">No workouts logged yet. Add one from the Log tab.</p>';
      return;
    }

    // Render a sticky header row then one row per workout; index is used for deletion
    container.innerHTML = `
      <div class="history-header">
        <span>Date</span><span>Type</span><span>Distance</span>
        <span>Split</span><span>Rate</span><span>Notes</span><span></span>
      </div>
      ${workouts.map((w, i) => `
        <div class="workout-row" id="row-${i}">
          <span class="date">${w.date}</span>
          <span><span class="type-badge ${w.type}">${w.type.replace('_',' ')}</span></span>
          <span class="dist">${w.distance_m.toLocaleString()}m</span>
          <span class="split">${formatSplit(w.avg_split_sec)}</span>
          <span class="rate">${w.stroke_rate} spm</span>
          <span class="notes">${w.notes || '—'}</span>
          <button class="btn-delete" title="Delete" onclick="deleteWorkout(${i})">✕</button>
        </div>
      `).join('')}
    `;
  } catch (e) {
    container.innerHTML = '<p class="empty-state">Failed to load workouts.</p>';
  }
}

async function deleteWorkout(index) {
  if (!confirm('Delete this workout?')) return;
  await fetch(`/api/workouts/${index}`, { method: 'DELETE' });
  // Refresh both views so stats and history stay in sync after deletion
  loadHistory();
  loadDashboard();
}

async function loadAnalytics() {
  const container = document.getElementById('summary-cards');
  container.innerHTML = '<p class="empty-state">Loading…</p>';

  try {
    const res = await fetch('/api/summary');
    const summary = await res.json();

    if (!summary.length) {
      container.innerHTML = '<p class="empty-state">No workout data yet.</p>';
      return;
    }

    container.innerHTML = summary.map(s => `
      <div class="summary-card">
        <h3 style="color:${TYPE_COLORS[s.type] ?? 'var(--text)'}">${s.type.replace(/_/g,' ')}</h3>
        <div class="summary-stat"><span class="key">Sessions</span><span class="val">${s.count}</span></div>
        <div class="summary-stat"><span class="key">Total Distance</span><span class="val">${s.total_distance_m.toLocaleString()}m</span></div>
        <div class="summary-stat"><span class="key">Avg Split</span><span class="val">${s.avg_split_fmt}/500m</span></div>
        <div class="summary-stat"><span class="key">Avg Stroke Rate</span><span class="val">${s.avg_stroke_rate} spm</span></div>
        <div class="summary-stat"><span class="key">Best Split</span><span class="val">${s.best_split_fmt}/500m</span></div>
        <div class="summary-stat"><span class="key">Best Split Date</span><span class="val">${s.best_split_date}</span></div>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = '<p class="empty-state">Failed to load analytics.</p>';
  }
}

// Default the date picker to today so users don't have to type it manually
document.getElementById('f-date').value = new Date().toISOString().slice(0,10);

document.getElementById('btn-add').addEventListener('click', async () => {
  const msg = document.getElementById('form-msg');
  const date      = document.getElementById('f-date').value;
  const type      = document.getElementById('f-type').value;
  const distance  = document.getElementById('f-distance').value;
  const splitRaw  = document.getElementById('f-split').value.trim();
  const rate      = document.getElementById('f-rate').value;
  const notes     = document.getElementById('f-notes').value.trim();

  // Validate split format client-side before hitting the server
  const splitSec = parseSplit(splitRaw);
  if (!splitSec) {
    showMsg(msg, 'Invalid split — use m:ss format like 2:10', 'err');
    return;
  }

  if (!date || !distance || !rate) {
    showMsg(msg, 'Please fill in all required fields.', 'err');
    return;
  }

  const body = {
    date,
    type,
    distance_m: parseInt(distance),
    avg_split_sec: splitSec,
    stroke_rate: parseInt(rate),
    notes,
  };

  try {
    const res = await fetch('/api/workouts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (res.ok) {
      showMsg(msg, '✓ Workout saved!', 'ok');
      // Clear variable fields; leave date and type as likely defaults for the next entry
      document.getElementById('f-distance').value = '';
      document.getElementById('f-split').value = '';
      document.getElementById('f-rate').value = '';
      document.getElementById('f-notes').value = '';
      loadDashboard();
    } else {
      const err = await res.json();
      showMsg(msg, err.error ?? 'Failed to save.', 'err');
    }
  } catch (e) {
    showMsg(msg, 'Network error.', 'err');
  }
});

document.getElementById('btn-sample').addEventListener('click', async () => {
  if (!confirm('Load sample data? This will add 15 sample workouts.')) return;
  await fetch('/api/sample', { method: 'POST' });
  loadDashboard();
});

document.getElementById('btn-clear').addEventListener('click', async () => {
  if (!confirm('Delete ALL workout data? This cannot be undone.')) return;
  await fetch('/api/clear', { method: 'POST' });
  loadDashboard();
  // Destroy the chart instance so a stale chart isn't left in memory
  if (splitChart) { splitChart.destroy(); splitChart = null; }
});

function parseSplit(text) {
  // Expects exactly "m:ss"; rejects if seconds are out of the 0–59 range
  const parts = text.split(':');
  if (parts.length !== 2) return null;
  const m = parseInt(parts[0]);
  const s = parseInt(parts[1]);
  if (isNaN(m) || isNaN(s) || s < 0 || s >= 60) return null;
  return m * 60 + s;
}

function formatSplit(sec) {
  // Mirrors the Python format_split helper: seconds → "m:ss"
  sec = Math.round(sec);
  return `${Math.floor(sec/60)}:${String(sec%60).padStart(2,'0')}`;
}

function showMsg(el, text, cls) {
  el.textContent = text;
  el.className = 'form-msg ' + cls;
  // Auto-clear success messages after 3 s; leave error messages until next action
  if (cls === 'ok') setTimeout(() => { el.textContent = ''; el.className = 'form-msg'; }, 3000);
}

loadDashboard();
