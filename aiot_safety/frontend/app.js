const API = 'http://localhost:3001';

// ===== 時鐘 =====
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('zh-TW', { hour12: false });
  document.getElementById('date').textContent = now.toLocaleDateString('zh-TW', {
    year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short',
  });
}
setInterval(updateClock, 1000);
updateClock();

// ===== Toast =====
function showToast(msg, type = 'info') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type} show`;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 3500);
}

// ===== Health Check =====
async function checkHealth() {
  const pill = document.getElementById('apiStatus');
  try {
    const res = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) });
    const ok = res.ok;
    pill.className = `status-pill ${ok ? 'online' : 'offline'}`;
    pill.querySelector('.status-text').textContent = ok ? 'API 連線正常' : 'API 異常';
  } catch {
    pill.className = 'status-pill offline';
    pill.querySelector('.status-text').textContent = 'API 無法連線';
  }
}

// ===== Chart Setup =====
const PALETTE = [
  '#00d4ff','#00ff88','#ffb800','#a855f7','#ff4757',
  '#3ecf8e','#f97316','#06b6d4','#ec4899','#84cc16',
];
let chart = null;

function initChart() {
  const ctx = document.getElementById('categoryChart').getContext('2d');
  chart = new Chart(ctx, {
    type: 'doughnut',
    data: { labels: [], datasets: [{ data: [], backgroundColor: PALETTE, borderColor: 'transparent', borderWidth: 0, hoverOffset: 8 }] },
    options: {
      responsive: true, maintainAspectRatio: true,
      cutout: '68%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(13,21,37,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          padding: 12,
          callbacks: {
            label: (ctx) => ` ${ctx.parsed} 次 (${((ctx.parsed / ctx.dataset.data.reduce((a,b) => a+b,0)) * 100).toFixed(1)}%)`,
          },
        },
      },
      animation: { animateScale: true, duration: 600, easing: 'easeOutQuart' },
    },
  });
}

function updateChart(categories) {
  const labels = Object.keys(categories);
  const data = Object.values(categories);
  chart.data.labels = labels;
  chart.data.datasets[0].data = data;
  chart.data.datasets[0].backgroundColor = PALETTE.slice(0, labels.length);
  chart.update('active');

  // Legend
  const legend = document.getElementById('chartLegend');
  const total = data.reduce((a, b) => a + b, 0);
  legend.innerHTML = labels.map((lbl, i) => `
    <div class="legend-item">
      <div class="legend-left">
        <div class="legend-dot" style="background:${PALETTE[i]}"></div>
        <span class="legend-name">${lbl}</span>
      </div>
      <span class="legend-count">${data[i]} · ${((data[i]/total)*100).toFixed(1)}%</span>
    </div>
  `).join('');
}

// ===== Stats =====
async function fetchStats() {
  try {
    const res = await fetch(`${API}/api/detections/stats`);
    const { total, categories } = await res.json();

    document.getElementById('valTotal').textContent = total.toLocaleString();

    const classCount = Object.keys(categories).length;
    document.getElementById('valClasses').textContent = classCount;

    const top = Object.entries(categories).sort((a, b) => b[1] - a[1])[0];
    document.getElementById('valTop').textContent = top ? `${top[0]} (${top[1]}次)` : '—';

    if (classCount > 0) updateChart(categories);
  } catch {
    // silent
  }
}

// ===== Detections Feed =====
function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString('zh-TW', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function confColor(conf) {
  if (conf >= 0.8) return '#00ff88';
  if (conf >= 0.5) return '#ffb800';
  return '#ff4757';
}

async function fetchDetections() {
  try {
    const res = await fetch(`${API}/api/detections?limit=50`);
    const rows = await res.json();

    const tbody = document.getElementById('detectionBody');

    if (!rows.length) {
      tbody.innerHTML = '<tr class="placeholder-row"><td colspan="4">尚無偵測資料</td></tr>';
      return;
    }

    tbody.innerHTML = rows.map((r) => {
      const conf = r.confidence;
      const barW = Math.round(conf * 80);
      const color = confColor(conf);
      return `
        <tr>
          <td>${formatTime(r.timestamp)}</td>
          <td><span class="class-badge">${r.className}</span></td>
          <td>
            <div class="conf-bar-wrap">
              <div class="conf-bar" style="width:${barW}px;background:${color}"></div>
              <span class="conf-val" style="color:${color}">${(conf * 100).toFixed(0)}%</span>
            </div>
          </td>
          <td><span class="device-tag">${r.deviceId}</span></td>
        </tr>`;
    }).join('');
  } catch {
    // silent
  }
}

// ===== Audits =====
function formatDateTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
}

async function fetchAudits() {
  try {
    const res = await fetch(`${API}/api/analysis/audits`);
    const audits = await res.json();

    document.getElementById('auditCount').textContent = `${audits.length} 筆`;

    if (!audits.length) {
      document.getElementById('auditList').innerHTML = '<div class="empty-state">尚無稽核報告</div>';
      document.getElementById('valAudit').textContent = '—';
      return;
    }

    document.getElementById('valAudit').textContent = formatDateTime(audits[0].createdAt);

    document.getElementById('auditList').innerHTML = audits.map((a, i) => `
      <div class="audit-item" onclick="toggleAudit(this)">
        <div class="audit-meta">
          <span class="audit-time">${formatDateTime(a.createdAt)}</span>
          <span class="audit-violations">${a.violationCount} 次違規</span>
        </div>
        <div class="audit-summary">${a.reportContent.split('\n')[0]}</div>
        <div class="audit-report">${a.reportContent}</div>
      </div>
    `).join('');
  } catch {
    // silent
  }
}

function toggleAudit(el) {
  el.classList.toggle('expanded');
}

// ===== Run Audit Button =====
document.getElementById('btnAudit').addEventListener('click', async () => {
  const btn = document.getElementById('btnAudit');
  btn.disabled = true;
  btn.textContent = '產生中…';
  try {
    const res = await fetch(`${API}/api/analysis/audit`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message || '✅ 稽核報告已產生', 'success');
      await fetchAudits();
      await fetchStats();
    } else {
      showToast(`❌ ${data.error || '稽核失敗'}`, 'error');
    }
  } catch (e) {
    showToast('❌ 無法連線至 API', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
    </svg> 產生稽核報告`;
  }
});

// ===== Init & Polling =====
async function refresh() {
  await checkHealth();
  await Promise.all([fetchStats(), fetchDetections(), fetchAudits()]);
}

initChart();
refresh();
setInterval(refresh, 5000);
