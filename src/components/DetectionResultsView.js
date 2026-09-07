/**
 * MarineDebrisAI - Detection Results View
 * Professional scientific layout with image viewer and structured detection table
 */

import { formatCoordinates } from '../services/geoService.js';
import { downloadJsonReport, downloadCsvReport } from '../services/reportExporter.js';

export function renderDetectionResultsView({ scanData, onReanalyze }) {
  const container = document.createElement('div');
  container.className = 'detection-results-view';

  if (!scanData || !scanData.detections) {
    container.innerHTML = `
      <div class="panel" style="text-align: center; padding: 60px 20px;">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--border-strong)" stroke-width="1.5" style="margin: 0 auto 16px;">
          <circle cx="12" cy="12" r="10"/><path d="m10 15 5-3-5-3v6z"/>
        </svg>
        <h2 style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px;">No Detection Results Available</h2>
        <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 20px;">
          Upload a sonar scan on the Dashboard or Sonar Analysis page to run YOLO detection.
        </p>
        <button class="btn btn-primary" id="goToAnalysisBtn">Go to Sonar Analysis →</button>
      </div>
    `;
    container.querySelector('#goToAnalysisBtn')?.addEventListener('click', onReanalyze);
    return container;
  }

  const detections = scanData.detections || [];
  const imageDim = scanData.image_dimensions || { width: 1024, height: 1024 };

  // Viewer state
  let zoomLevel = 1.0;

  container.innerHTML = `
    <!-- Top Action Bar -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; background: #ffffff; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 12px 20px; box-shadow: var(--shadow-sm); flex-wrap: wrap; gap: 12px;">
      <div style="display: flex; align-items: center; gap: 12px; font-size: 13px;">
        <span class="badge badge-green">${detections.length} ${detections.length === 1 ? 'Target Detected' : 'Targets Detected'}</span>
        <span style="color: var(--text-muted);">File:</span>
        <span style="font-weight: 600; color: var(--text-primary);">${scanData.filename || 'sonar_image.jpg'}</span>
        <span style="color: var(--text-muted);">Inference Time:</span>
        <span style="font-family: var(--font-mono);">${scanData.inference_seconds ? scanData.inference_seconds + 's' : (scanData.total_processing_seconds ? scanData.total_processing_seconds + 's' : '0.16s')}</span>
      </div>

      <div style="display: flex; align-items: center; gap: 8px;">
        <button class="btn btn-secondary btn-sm" id="btnExportJson">Export JSON</button>
        <button class="btn btn-secondary btn-sm" id="btnExportCsv">Export CSV</button>
      </div>
    </div>

    <!-- Image Viewer Section -->
    <div class="panel" style="margin-bottom: 20px; padding: 0; overflow: hidden;">
      <div class="sonar-stage-toolbar">
        <div class="toolbar-group">
          <span style="font-size: 12.5px; font-weight: 600; color: var(--text-secondary);">Acoustic Detection Viewer</span>
          <span style="font-size: 11.5px; color: var(--text-muted);">(${imageDim.width} × ${imageDim.height} px)</span>
        </div>
        <div class="toolbar-group">
          <button class="stage-btn" id="zoomMinusBtn" title="Zoom Out">−</button>
          <span style="font-family: var(--font-mono); font-size: 12px; min-width: 44px; text-align: center;" id="zoomText">100%</span>
          <button class="stage-btn" id="zoomPlusBtn" title="Zoom In">+</button>
          <button class="stage-btn" id="zoomResetBtn">Reset</button>
        </div>
      </div>

      <div style="background: var(--color-bg-dark); display: flex; align-items: center; justify-content: center; min-height: 420px; max-height: 520px; overflow: hidden; position: relative;">
        <div id="resultsCanvasWrapper" style="transition: transform 0.15s ease; display: flex; align-items: center; justify-content: center;">
          <img id="resultsMainImg" src="${scanData.annotated_image_url || scanData.image_url}" alt="YOLO Annotated Sonar Scan" style="max-width: 100%; max-height: 500px; object-fit: contain; display: block;" />
        </div>
      </div>
    </div>

    <!-- Detection Table (Normal Professional Scientific Table) -->
    <div class="panel" style="padding: 0; overflow: hidden;">
      <div style="padding: 16px 20px; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center;">
        <h3 style="font-size: 14px; font-weight: 700; color: var(--text-primary);">
          Identified Target Anomaly Records (${detections.length})
        </h3>
        <span style="font-size: 12px; color: var(--text-muted);">Evaluated with YOLO best.pt</span>
      </div>

      <div class="data-table-container" style="border: none; border-radius: 0;">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Classification</th>
              <th>Confidence</th>
              <th>Location / GPS</th>
              <th>Bounding Box [x1, y1, x2, y2]</th>
              <th>Dimensions</th>
              <th>Anomaly Assessment</th>
            </tr>
          </thead>
          <tbody>
            ${detections.map(d => {
              const classType = (d.classification || 'other').toLowerCase();
              return `
                <tr>
                  <td class="mono" style="font-weight: 700; color: var(--color-primary);">${d.id}</td>
                  <td><span class="detection-class-badge class-${classType}">${d.classification.toUpperCase()}</span></td>
                  <td class="mono" style="font-weight: 600; color: ${d.confidence >= 80 ? 'var(--color-success)' : 'var(--color-warning)'};">
                    ${d.confidence.toFixed(1)}%
                  </td>
                  <td class="mono" style="font-size: 12px;">
                    ${d.latitude !== null && d.latitude !== undefined ? formatCoordinates(d.latitude, d.longitude) : '<span style="color: var(--text-muted);">N/A (No footprint)</span>'}
                  </td>
                  <td class="mono" style="font-size: 11.5px;">[${d.bounding_box?.x1}, ${d.bounding_box?.y1}, ${d.bounding_box?.x2}, ${d.bounding_box?.y2}]</td>
                  <td class="mono" style="font-size: 12px;">${d.width_pixels} × ${d.height_pixels} px</td>
                  <td style="font-size: 12px;">
                    ${d.anomaly_score !== null && d.anomaly_score !== undefined ? `<strong>${d.anomaly_score.toFixed(1)}%</strong> (${d.anomaly_assessment || 'Moderate'})` : 'N/A'}
                  </td>
                </tr>
              `;
            }).join('')}

            ${detections.length === 0 ? `
              <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-muted);">
                  Zero objects detected in this sonar scan.
                </td>
              </tr>
            ` : ''}
          </tbody>
        </table>
      </div>
    </div>
  `;

  // Zoom controls
  const imgWrapper = container.querySelector('#resultsCanvasWrapper');
  const zoomText = container.querySelector('#zoomText');

  const updateZoom = () => {
    imgWrapper.style.transform = `scale(${zoomLevel})`;
    zoomText.textContent = `${Math.round(zoomLevel * 100)}%`;
  };

  container.querySelector('#zoomPlusBtn').addEventListener('click', () => {
    zoomLevel = Math.min(zoomLevel + 0.25, 3.0);
    updateZoom();
  });

  container.querySelector('#zoomMinusBtn').addEventListener('click', () => {
    zoomLevel = Math.max(zoomLevel - 0.25, 0.5);
    updateZoom();
  });

  container.querySelector('#zoomResetBtn').addEventListener('click', () => {
    zoomLevel = 1.0;
    updateZoom();
  });

  // Export handlers
  container.querySelector('#btnExportJson').addEventListener('click', () => {
    downloadJsonReport(scanData);
  });

  container.querySelector('#btnExportCsv').addEventListener('click', () => {
    downloadCsvReport(scanData);
  });

  return container;
}
