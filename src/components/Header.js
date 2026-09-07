/**
 * MarineDebrisAI - Header Component
 * Clean, practical header with model status and image indicator
 */

import { checkBackendHealth } from '../services/api.js';

let clockIntervalId = null;

export function renderHeader(viewTitle, viewSubtitle, currentAnalysis = null) {
  const container = document.createElement('header');
  container.className = 'app-header';

  container.innerHTML = `
    <div class="header-left">
      <div class="view-heading-group">
        <h1 class="view-title" id="pageTitle">${viewTitle}</h1>
        <span class="view-subtitle" id="pageSubtitle">${viewSubtitle}</span>
      </div>
    </div>

    <div class="header-right">
      ${currentAnalysis ? `
        <div class="header-pill">
          <span style="color: var(--text-muted);">Active Scan:</span>
          <span class="header-pill-highlight">${currentAnalysis.filename || 'sonar_image.jpg'}</span>
        </div>
      ` : ''}

      <!-- Real AI Status Indicator -->
      <div class="header-pill" id="aiStatusPill">
        <span class="status-dot" id="aiStatusDot"></span>
        <span id="aiStatusText">AI Connected (best.pt)</span>
      </div>

      <div class="header-clock" id="headerClock">--:--:--</div>
    </div>
  `;

  // Clock
  const updateClock = () => {
    const el = container.querySelector('#headerClock');
    if (el) el.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  updateClock();
  if (clockIntervalId) clearInterval(clockIntervalId);
  clockIntervalId = setInterval(updateClock, 1000);

  // Check health once on render
  checkBackendHealth().then(res => {
    const textEl = container.querySelector('#aiStatusText');
    const dotEl = container.querySelector('#aiStatusDot');
    const pillEl = container.querySelector('#aiStatusPill');

    if (res.connected) {
      if (textEl) textEl.textContent = 'AI Connected (best.pt)';
      if (dotEl) {
        dotEl.style.backgroundColor = 'var(--color-success)';
      }
      if (pillEl) {
        pillEl.style.borderColor = 'var(--border-subtle)';
      }
    } else {
      if (textEl) textEl.textContent = 'AI Offline';
      if (dotEl) {
        dotEl.style.backgroundColor = 'var(--color-danger)';
      }
      if (pillEl) {
        pillEl.style.borderColor = 'var(--color-danger-border)';
        pillEl.title = 'Python backend (api_server.py) is not running on http://127.0.0.1:8000';
      }
    }
  });

  return container;
}
