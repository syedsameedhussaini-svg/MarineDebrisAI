/**
 * MarineDebrisAI - Reports View
 * Simple professional detection summary and CSV/JSON export service
 */

import { formatCoordinates } from '../services/geoService.js';
import { downloadJsonReport, downloadCsvReport } from '../services/reportExporter.js';

export function renderReportsView({ scanData }) {
  const container = document.createElement('div');
  container.className = 'reports-view';

  const detections = scanData?.detections || [];

  container.innerHTML = `
    <!-- Top Action Bar -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
      <div>
        <h2 style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">Sonar Detection Report</h2>
        <p style="font-size: 13px; color: var(--text-muted);">
          Active scan: <span style="font-weight: 600; color: var(--color-primary);">${scanData?.filename || 'No scan loaded'}</span> · Total detections: <strong>${detections.length}</strong>
        </p>
      </div>

      <div style="display: flex; gap: 10px;">
        <button class="btn btn-primary btn-sm" id="btnExportJsonReport" ${!scanData ? 'disabled' : ''}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export JSON
        </button>
        <button class="btn btn-secondary btn-sm" id="btnExportCsvReport" ${!scanData ? 'disabled' : ''}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <!-- Professional Scientific Detection Table -->
    <div class="panel" style="padding: 0; overflow: hidden;">
      <div class="data-table-container" style="border: none; border-radius: 0;">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Classification</th>
              <th>Review Status</th>
              <th>Confidence</th>
              <th>Dimensions</th>
              <th>Anomaly Score</th>
              <th>Coordinates</th>
            </tr>
          </thead>
          <tbody>
            \${detections.map((d, index) => {
              const classType = (d.classification || 'other').toLowerCase();
              const revStatus = window.reviewStatusMap ? (window.reviewStatusMap[d.id] || d.review_status || 'Unverified') : (d.review_status || 'Unverified');
              const revBadgeClass = revStatus === 'Confirmed' ? 'badge-green' : (revStatus === 'Rejected' ? 'badge-red' : 'badge-amber');
              
              return \`
                <tr>
                  <td class="mono" style="color: var(--color-primary); font-weight: 700;">\${d.id}</td>
                  <td><span class="detection-class-badge class-\${classType.includes('shipwreck') ? 'shipwreck' : 'other'}">\${d.classification.toUpperCase()}</span></td>
                  <td><span class="badge \${revBadgeClass}">\${revStatus}</span></td>
                  <td class="mono" style="color: \${d.confidence >= 80 ? 'var(--color-success)' : 'var(--color-warning)'}; font-weight: 700;">
                    \${d.confidence.toFixed(1)}%
                  </td>
                  <td class="mono" style="font-size: 12px;">\${d.width_m ? \`\${d.width_m}m x \${d.length_m}m\` : \`\${d.width_pixels}x\${d.height_pixels} px\`}</td>
                  <td style="font-size: 12px;">\${d.anomaly_score !== null && d.anomaly_score !== undefined ? \`\${d.anomaly_score.toFixed(1)}% (\${d.anomaly_assessment || 'Moderate'})\` : 'N/A'}</td>
                  <td class="mono" style="font-size: 12px;">
                    \${d.latitude !== null && d.latitude !== undefined ? formatCoordinates(d.latitude, d.longitude) : '<span style="color: var(--text-muted);">N/A (No footprint)</span>'}
                  </td>
                </tr>
              \`;
            }).join('')}

            ${detections.length === 0 ? `
              <tr>
                <td colspan="8" style="text-align: center; padding: 48px; color: var(--text-muted);">
                  ${scanData ? 'No objects detected in this sonar scan.' : 'No detection records available. Run an analysis first.'}
                </td>
              </tr>
            ` : ''}
          </tbody>
        </table>
      </div>
    </div>
  `;

  // Download buttons
  container.querySelector('#btnExportJsonReport')?.addEventListener('click', () => {
    if (scanData) downloadJsonReport(scanData);
  });

  container.querySelector('#btnExportCsvReport')?.addEventListener('click', () => {
    if (scanData) downloadCsvReport(scanData);
  });

  return container;
}
