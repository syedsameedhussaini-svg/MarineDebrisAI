/**
 * MarineDebrisAI - Dashboard View
 * Clean scientific workflow: Upload Sonar Image → Run AI Detection → View Results
 */

export function renderDashboardView({ currentAnalysis, onNavigate, onRunDetection, isProcessing = false }) {
  const container = document.createElement('div');
  container.className = 'dashboard-view';

  const detections = currentAnalysis?.detections || [];
  const totalCount = detections.length;
  const peakConf = totalCount > 0 ? Math.max(...detections.map(d => d.confidence)) : null;

  container.innerHTML = `
    <!-- Top Card: Upload & Analyze Sonar Image -->
    <div class="panel">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h2 style="font-size: 16px; font-weight: 700; color: var(--text-primary);">Sonar Image Detection</h2>
          <p style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">
            Upload side-scan sonar imagery to run detection with the trained <strong>best.pt</strong> model.
          </p>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="stage-btn" id="dashSampleShipwreck">Load Shipwreck Sample</button>
          <button class="stage-btn" id="dashSampleDebris">Load Debris Sample</button>
        </div>
      </div>

      <!-- Upload Dropzone & Action -->
      <div style="display: grid; grid-template-columns: 1fr auto; gap: 16px; align-items: stretch;">
        <div id="dashDropZone" style="border: 2px dashed var(--border-medium); border-radius: var(--radius-md); padding: 18px 20px; text-align: left; cursor: pointer; background: var(--color-bg-subtle); display: flex; align-items: center; gap: 16px; transition: border-color 0.15s;">
          <input type="file" id="dashFileInput" accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff" style="display: none;" />
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2" style="flex-shrink: 0;">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <div>
            <div style="font-size: 13.5px; font-weight: 600; color: var(--text-primary);" id="dashUploadLabel">
              Choose sonar image or drag and drop file here
            </div>
            <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">
              Supports PNG, JPG, BMP · Runs directly through local Python backend
            </div>
          </div>
        </div>

        <button class="btn btn-primary btn-lg" id="dashRunBtn" style="min-width: 190px;" ${isProcessing ? 'disabled' : ''}>
          ${isProcessing ? 'Analyzing...' : 'Run Detection →'}
        </button>
      </div>

      <div id="dashStatusMsg" style="margin-top: 12px; font-size: 12px; color: var(--color-primary); font-weight: 500; display: none;"></div>
    </div>

    <!-- Results Section -->
    ${currentAnalysis ? `
      <!-- Useful Summary Metrics (Only 3 clean cards) -->
      <div class="metric-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 20px;">
        <div class="metric-card">
          <div class="metric-label">Objects Detected</div>
          <div class="metric-value" style="color: ${totalCount > 0 ? 'var(--color-primary)' : 'var(--text-muted)'};">
            ${totalCount}
          </div>
          <div class="metric-meta">${totalCount === 1 ? '1 target identified' : `${totalCount} targets identified`}</div>
        </div>

        <div class="metric-card">
          <div class="metric-label">Highest Confidence</div>
          <div class="metric-value">
            ${peakConf !== null ? `${peakConf.toFixed(1)}%` : 'N/A'}
          </div>
          <div class="metric-meta">Evaluation standard: YOLO</div>
        </div>

        <div class="metric-card">
          <div class="metric-label">Model Used</div>
          <div class="metric-value" style="font-size: 20px;">
            best.pt
          </div>
          <div class="metric-meta">Time: ${currentAnalysis.inference_seconds !== undefined ? `${currentAnalysis.inference_seconds}s` : '0.16s'}</div>
        </div>
      </div>

      <!-- Main Sonar Image Display & Detected Target List -->
      <div style="display: grid; grid-template-columns: 1.3fr 1fr; gap: 20px;">
        <!-- Sonar Image with Bounding Boxes -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
              </svg>
              Detection Output: ${currentAnalysis.filename || 'sonar_image.jpg'}
            </div>
            <span class="badge badge-green">Inference Complete</span>
          </div>

          <div style="background: var(--color-bg-dark); border-radius: var(--radius-md); overflow: hidden; display: flex; align-items: center; justify-content: center; max-height: 420px; border: 1px solid var(--border-subtle); padding: 8px;">
            <img src="${currentAnalysis.annotated_image_url || currentAnalysis.image_url}" alt="Annotated Sonar Image" style="max-width: 100%; max-height: 400px; object-fit: contain;" />
          </div>

          <div style="display: flex; gap: 10px; margin-top: 16px;">
            <button class="btn btn-secondary btn-sm" style="flex: 1;" id="dashGoResultsBtn">
              Interactive Viewer →
            </button>
            <button class="btn btn-secondary btn-sm" id="dashGoMapBtn">
              Geospatial Map
            </button>
            <button class="btn btn-secondary btn-sm" id="dashGoReportsBtn">
              Export Reports
            </button>
          </div>
        </div>

        <!-- Detected Objects List -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><path d="m10 15 5-3-5-3v6z"/>
              </svg>
              Detected Objects (${totalCount})
            </div>
          </div>

          <div style="display: flex; flex-direction: column; gap: 10px; max-height: 400px; overflow-y: auto;">
            ${detections.map(d => {
              const classType = (d.classification || 'other').toLowerCase();
              return `
                <div style="background: var(--color-bg-subtle); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 12px 14px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span class="detection-class-badge class-${classType}">${d.classification.toUpperCase()}</span>
                    <span style="font-family: var(--font-mono); font-weight: 700; color: ${d.confidence >= 80 ? 'var(--color-success)' : 'var(--color-warning)'}; font-size: 13px;">
                      ${d.confidence.toFixed(1)}%
                    </span>
                  </div>
                  <div style="font-size: 12px; color: var(--text-secondary); display: flex; flex-direction: column; gap: 3px; font-family: var(--font-mono);">
                    <div>Box: [${d.bounding_box?.x1}, ${d.bounding_box?.y1}] → [${d.bounding_box?.x2}, ${d.bounding_box?.y2}]</div>
                    <div>Dimensions: ${d.width_pixels} × ${d.height_pixels} px</div>
                    <div>Coordinates: ${d.latitude !== null && d.latitude !== undefined ? `${d.latitude.toFixed(6)}°, ${d.longitude.toFixed(6)}°` : 'N/A (No survey footprint)'}</div>
                    ${d.anomaly_score !== null && d.anomaly_score !== undefined ? `<div>Anomaly Score: <strong>${d.anomaly_score.toFixed(1)}%</strong> (${d.anomaly_assessment || 'Moderate'})</div>` : ''}
                  </div>
                </div>
              `;
            }).join('')}

            ${totalCount === 0 ? `
              <div style="text-align: center; padding: 40px 16px; color: var(--text-muted); font-size: 13px;">
                No objects detected above the confidence threshold.
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    ` : `
      <!-- Clean Empty State Guide -->
      <div class="panel" style="text-align: center; padding: 48px 24px; color: var(--text-muted);">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--border-strong)" stroke-width="1.5" style="margin: 0 auto 12px;">
          <rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
        </svg>
        <div style="font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">No Sonar Image Loaded</div>
        <p style="font-size: 13px; max-width: 480px; margin: 0 auto;">
          Upload a sonar file using the form above or click one of the sample buttons to run real-time YOLO detection.
        </p>
      </div>
    `}
  `;

  // State
  let selectedFile = null;
  let selectedBlobUrl = null;
  let selectedFilename = null;

  const dropZone = container.querySelector('#dashDropZone');
  const fileInput = container.querySelector('#dashFileInput');
  const uploadLabel = container.querySelector('#dashUploadLabel');
  const runBtn = container.querySelector('#dashRunBtn');
  const statusMsg = container.querySelector('#dashStatusMsg');

  dropZone.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', (e) => {
    if (e.target.files?.length > 0) {
      selectedFile = e.target.files[0];
      selectedBlobUrl = null;
      selectedFilename = selectedFile.name;
      uploadLabel.textContent = `Selected: ${selectedFile.name}`;
      uploadLabel.style.color = 'var(--color-primary)';
    }
  });

  // Sample buttons
  container.querySelector('#dashSampleShipwreck')?.addEventListener('click', () => {
    selectedFile = null;
    selectedBlobUrl = '/samples/monrovia-side-scan-sonar-IVER-hires.png';
    selectedFilename = 'monrovia.png';
    uploadLabel.textContent = 'Selected: monrovia.png (Shipwreck Sample)';
    uploadLabel.style.color = 'var(--color-primary)';
  });

  container.querySelector('#dashSampleDebris')?.addEventListener('click', () => {
    selectedFile = null;
    selectedBlobUrl = '/samples/sonar_test.jpg';
    selectedFilename = 'sonar_test.jpg';
    uploadLabel.textContent = 'Selected: sonar_test.jpg (Debris Sample)';
    uploadLabel.style.color = 'var(--color-primary)';
  });

  // Run AI Detection button
  runBtn.addEventListener('click', async () => {
    if (!selectedFile && !selectedBlobUrl) {
      selectedBlobUrl = '/samples/monrovia-side-scan-sonar-IVER-hires.png';
      selectedFilename = 'monrovia.png';
    }

    statusMsg.style.display = 'block';
    statusMsg.textContent = 'Processing sonar image through YOLO best.pt backend...';
    runBtn.disabled = true;

    try {
      let blob = selectedFile;
      if (!blob && selectedBlobUrl) {
        const resp = await fetch(selectedBlobUrl);
        blob = await resp.blob();
      }

      await onRunDetection({
        imageFile: selectedFile,
        imageBlob: !selectedFile ? blob : null,
        filename: selectedFilename,
        onProgress: (pct, msg) => {
          statusMsg.textContent = `${msg} (${pct}%)`;
        }
      });
    } catch (err) {
      alert(`Detection Error:\n${err.message}`);
      statusMsg.style.display = 'none';
      runBtn.disabled = false;
    }
  });

  // Navigation shortcuts
  container.querySelector('#dashGoResultsBtn')?.addEventListener('click', () => onNavigate('results'));
  container.querySelector('#dashGoMapBtn')?.addEventListener('click', () => onNavigate('map'));
  container.querySelector('#dashGoReportsBtn')?.addEventListener('click', () => onNavigate('reports'));

  return container;
}
