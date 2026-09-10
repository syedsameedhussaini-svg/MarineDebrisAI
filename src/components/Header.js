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

  const updateAiStatus = async () => {
    const textEl = container.querySelector('#aiStatusText');
    const dotEl = container.querySelector('#aiStatusDot');
    const pillEl = container.querySelector('#aiStatusPill');
    if (!pillEl) return;

    const res = await checkBackendHealth(10000);
    if (res.connected) {
      if (textEl) textEl.textContent = 'AI Connected (best.pt)';
      if (dotEl) dotEl.style.backgroundColor = 'var(--color-success)';
      if (pillEl) {
        pillEl.style.borderColor = 'var(--border-subtle)';
        pillEl.title = 'Python backend is connected and ready';
      }
    } else {
      if (textEl) textEl.textContent = 'AI Offline (Tap to retry)';
      if (dotEl) dotEl.style.backgroundColor = 'var(--color-danger)';
      if (pillEl) {
        pillEl.style.borderColor = 'var(--color-danger-border)';
        pillEl.title = 'Tap to test connection to backend';
      }
    }
  };

  updateAiStatus();

  // Auto-retry polling if offline every 10s
  const pollInterval = setInterval(() => {
    const textEl = container.querySelector('#aiStatusText');
    if (textEl && textEl.textContent.includes('Offline')) {
      updateAiStatus();
    }
  }, 10000);

  // Click pill to manually retry
  const pillEl = container.querySelector('#aiStatusPill');
  if (pillEl) {
    pillEl.style.cursor = 'pointer';
    pillEl.addEventListener('click', () => {
      const textEl = container.querySelector('#aiStatusText');
      if (textEl) textEl.textContent = 'Checking...';
      updateAiStatus();
    });
  }

  return container;
}
