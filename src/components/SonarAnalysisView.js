/**
 * MarineDebrisAI - Sonar Analysis View
 * Clean scientific workflow focused on the sonar image and inference controls
 */

import { runRealSonarAnalysis, checkBackendHealth } from '../services/api.js';

export function renderSonarAnalysisView({ onAnalysisComplete, currentAnalysis = null }) {
  const container = document.createElement('div');
  container.className = 'analysis-view';

  let selectedFile = null;
  let selectedBlobUrl = currentAnalysis?.image_url || '/samples/monrovia-side-scan-sonar-IVER-hires.png';
  let selectedFilename = currentAnalysis?.filename || 'monrovia.png';
  let isRunning = false;

  let confThreshold = 0.25;
  let iouThreshold = 0.45;

  container.innerHTML = `
    <!-- Offline Alert -->
    <div id="sonarBackendWarning" class="alert alert-danger" style="display: none;">
      <strong>Backend Offline:</strong> Python server is not responding on <code>http://127.0.0.1:8000</code>.
      Start it in terminal with <code>python api_server.py</code> to execute YOLO detections.
    </div>

    <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px;">
      
      <!-- Left: Image Selection & Preview -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Sonar Imagery Input
          </div>
          <div style="display: flex; gap: 6px;">
            <button class="stage-btn active" id="btnSonarShipwreck">Shipwreck Sample</button>
            <button class="stage-btn" id="btnSonarDebris">Debris Sample</button>
          </div>
        </div>

        <div id="sonarDropZone" style="border: 2px dashed var(--border-medium); border-radius: var(--radius-md); padding: 20px; text-align: center; cursor: pointer; background: var(--color-bg-subtle); margin-bottom: 16px;">
          <input type="file" id="sonarFileInput" accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff" style="display: none;" />
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2" style="margin: 0 auto 8px;">
            <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
          </svg>
          <div style="font-size: 13px; font-weight: 600; color: var(--text-primary);" id="sonarFileLabel">
            ${selectedFilename ? `Selected: ${selectedFilename}` : 'Click to select or drag and drop sonar scan'}
          </div>
          <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 2px;">
            PNG, JPG, BMP · Evaluated directly by trained YOLO model
          </div>
        </div>

        <!-- Preview on Neutral Slate Mat -->
        <div style="background: var(--color-bg-dark); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 8px; display: flex; align-items: center; justify-content: center; max-height: 300px; overflow: hidden;">
          <img id="sonarPreviewImg" src="${selectedBlobUrl}" alt="Preview" style="max-height: 280px; max-width: 100%; object-fit: contain;" />
        </div>
      </div>

      <!-- Right: Detection Controls & Status -->
      <div style="display: flex; flex-direction: column; gap: 20px;">
        
        <!-- Controls -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="4" x2="20" y1="21" y2="21"/><line x1="4" x2="20" y1="3" y2="3"/><line x1="12" x2="12" y1="21" y2="3"/>
              </svg>
              Analysis Parameters
            </div>
            <span class="badge badge-cyan">best.pt</span>
          </div>

          <div class="form-group" style="margin-bottom: 18px;">
            <div class="form-label">
              <span>Confidence Threshold</span>
              <span class="telemetry-val" id="sonarConfDisplay">${(confThreshold * 100).toFixed(0)}%</span>
            </div>
            <input type="range" min="0.10" max="0.95" step="0.05" value="${confThreshold}" class="form-range" id="sonarConfSlider" />
            <span style="font-size: 11.5px; color: var(--text-muted); margin-top: 3px; display: block;">Lower threshold detects more candidate objects; higher filters low confidence.</span>
          </div>

          <!-- Optional Survey Footprint Coordinates -->
          <details style="margin-bottom: 20px; font-size: 12.5px; color: var(--text-secondary);">
            <summary style="cursor: pointer; color: var(--color-primary); font-weight: 600; margin-bottom: 10px;">
              + Optional: Survey Footprint Coordinates (for GPS)
            </summary>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: var(--color-bg-subtle); padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label" style="font-size: 11px;">Min Latitude</label>
                <input type="number" step="0.00001" class="form-input" id="fpLatMin" value="34.0150" style="padding: 6px; font-size: 12px;" />
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label" style="font-size: 11px;">Max Latitude</label>
                <input type="number" step="0.00001" class="form-input" id="fpLatMax" value="34.0280" style="padding: 6px; font-size: 12px;" />
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label" style="font-size: 11px;">Min Longitude</label>
                <input type="number" step="0.00001" class="form-input" id="fpLonMin" value="-76.8400" style="padding: 6px; font-size: 12px;" />
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label" style="font-size: 11px;">Max Longitude</label>
                <input type="number" step="0.00001" class="form-input" id="fpLonMax" value="-76.8250" style="padding: 6px; font-size: 12px;" />
              </div>
            </div>
          </details>

          <button class="btn btn-primary btn-lg" id="sonarRunBtn" style="width: 100%;">
            Run AI Analysis
          </button>
        </div>

        <!-- Status Card -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/>
              </svg>
              Inference Status
            </div>
            <span class="badge ${currentAnalysis ? 'badge-green' : 'badge-cyan'}" id="sonarStatusBadge">
              ${currentAnalysis ? 'COMPLETED' : 'READY'}
            </span>
          </div>

          <div id="sonarStatusText" style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
            ${currentAnalysis ? `
              Last analysis: <strong>${currentAnalysis.filename}</strong><br/>
              Objects detected: <strong>${currentAnalysis.detections?.length || 0}</strong><br/>
              Inference time: <strong>${currentAnalysis.inference_seconds || currentAnalysis.total_processing_seconds}s</strong>
            ` : 'Ready to analyze. Click Run AI Analysis to begin inference.'}
          </div>
        </div>

      </div>

    </div>
  `;

  // Backend check
  checkBackendHealth().then(res => {
    const warning = container.querySelector('#sonarBackendWarning');
    if (warning) warning.style.display = res.connected ? 'none' : 'block';
  });

  // Slider
  const slider = container.querySelector('#sonarConfSlider');
  const confDisplay = container.querySelector('#sonarConfDisplay');
  slider.addEventListener('input', (e) => {
    confThreshold = parseFloat(e.target.value);
    confDisplay.textContent = `${(confThreshold * 100).toFixed(0)}%`;
  });

  // Sample buttons
  const btnShipwreck = container.querySelector('#btnSonarShipwreck');
  const btnDebris = container.querySelector('#btnSonarDebris');
  const previewImg = container.querySelector('#sonarPreviewImg');
  const fileLabel = container.querySelector('#sonarFileLabel');

  btnShipwreck.addEventListener('click', () => {
    btnShipwreck.classList.add('active');
    btnDebris.classList.remove('active');
    selectedFile = null;
    selectedBlobUrl = '/samples/monrovia-side-scan-sonar-IVER-hires.png';
    selectedFilename = 'monrovia.png';
    previewImg.src = selectedBlobUrl;
    fileLabel.textContent = 'Selected: monrovia.png (Shipwreck Sample)';
  });

  btnDebris.addEventListener('click', () => {
    btnDebris.classList.add('active');
    btnShipwreck.classList.remove('active');
    selectedFile = null;
    selectedBlobUrl = '/samples/sonar_test.jpg';
    selectedFilename = 'sonar_test.jpg';
    previewImg.src = selectedBlobUrl;
    fileLabel.textContent = 'Selected: sonar_test.jpg (Debris Sample)';
  });

  // Upload drop
  const dropZone = container.querySelector('#sonarDropZone');
  const fileInput = container.querySelector('#sonarFileInput');

  dropZone.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', (e) => {
    if (e.target.files?.length > 0) {
      selectedFile = e.target.files[0];
      selectedBlobUrl = URL.createObjectURL(selectedFile);
      selectedFilename = selectedFile.name;
      previewImg.src = selectedBlobUrl;
      fileLabel.textContent = `Selected: ${selectedFile.name}`;
      btnShipwreck.classList.remove('active');
      btnDebris.classList.remove('active');
    }
  });

  // Run Button
  const runBtn = container.querySelector('#sonarRunBtn');
  const statusBadge = container.querySelector('#sonarStatusBadge');
  const statusText = container.querySelector('#sonarStatusText');

  runBtn.addEventListener('click', async () => {
    if (isRunning) return;

    // Optional footprint
    const fpLatMin = parseFloat(container.querySelector('#fpLatMin').value);
    const fpLatMax = parseFloat(container.querySelector('#fpLatMax').value);
    const fpLonMin = parseFloat(container.querySelector('#fpLonMin').value);
    const fpLonMax = parseFloat(container.querySelector('#fpLonMax').value);

    const footprint = (!isNaN(fpLatMin) && !isNaN(fpLatMax) && !isNaN(fpLonMin) && !isNaN(fpLonMax)) ? {
      latitude_min: fpLatMin,
      latitude_max: fpLatMax,
      longitude_min: fpLonMin,
      longitude_max: fpLonMax
    } : null;

    isRunning = true;
    runBtn.disabled = true;
    statusBadge.textContent = 'RUNNING';
    statusBadge.className = 'badge badge-amber';
    statusText.textContent = 'Sending image to Python backend for YOLO best.pt inference...';

    try {
      let blob = selectedFile;
      if (!blob && selectedBlobUrl) {
        const resp = await fetch(selectedBlobUrl);
        blob = await resp.blob();
      }

      const result = await runRealSonarAnalysis({
        imageFile: selectedFile,
        imageBlob: !selectedFile ? blob : null,
        filename: selectedFilename,
        footprint: footprint,
        confidenceThreshold: confThreshold,
        iouThreshold: iouThreshold,
        onProgress: (pct, msg) => {
          statusText.textContent = `${msg} (${pct}%)`;
        }
      });

      statusBadge.textContent = 'COMPLETED';
      statusBadge.className = 'badge badge-green';
      statusText.innerHTML = `
        Completed successfully in <strong>${result.inference_seconds || result.total_processing_seconds}s</strong>.<br/>
        Objects detected: <strong>${result.detections?.length || 0}</strong>
      `;

      await new Promise(r => setTimeout(r, 200));

      if (onAnalysisComplete) {
        onAnalysisComplete(result);
      }
    } catch (err) {
      statusBadge.textContent = 'FAILED';
      statusBadge.className = 'badge badge-red';
      statusText.innerHTML = `<span style="color: var(--color-danger);">Error: ${err.message}</span>`;
      alert(`Detection Failed:\n${err.message}`);
    } finally {
      isRunning = false;
      runBtn.disabled = false;
    }
  });

  return container;
}
