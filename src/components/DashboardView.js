/**
 * MarineDebrisAI - Dashboard View
 * Modern Dark Mode scientific workflow (Physics-Aware Sonar Intelligence)
 */

export function renderDashboardView({ currentAnalysis, onNavigate, onRunDetection, isProcessing = false }) {
  const container = document.createElement('div');
  container.className = 'dashboard-view';

  const detections = currentAnalysis?.detections || [];
  const totalCount = detections.length;
  const peakConf = totalCount > 0 ? Math.max(...detections.map(d => d.confidence)) : null;

  // Add review functions to window so inline handlers work
  if (!window.reviewStatusMap) {
      window.reviewStatusMap = {};
  }
  
  window.updateReviewStatus = (detId, status, btnGroupElId, badgeElId) => {
      window.reviewStatusMap[detId] = status;
      
      const badge = document.getElementById(badgeElId);
      if (badge) {
          badge.textContent = status;
          badge.className = status === 'Confirmed' ? 'badge badge-green' : 'badge badge-red';
      }
      
      const btnGroup = document.getElementById(btnGroupElId);
      if (btnGroup) {
          btnGroup.innerHTML = `<span style="color: var(--text-muted); font-size: 12px; font-weight: 500;">Reviewed by Operator</span>`;
      }
      
      // Also update the source data object so exports have it
      if (currentAnalysis && currentAnalysis.detections) {
          const det = currentAnalysis.detections.find(d => d.id === detId);
          if (det) det.review_status = status;
      }
  };

  container.innerHTML = `
    <!-- Top Card: Upload & Analyze Sonar Image -->
    <div class="panel" style="border-top: 2px solid var(--color-primary);">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 16px;">
        <div>
          <h2 style="font-size: 20px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2" style="filter: drop-shadow(0 0 4px rgba(6,182,212,0.4));">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Sonar Image Inference
          </h2>
          <p style="font-size: 14px; color: var(--text-muted); margin-top: 6px;">
            Upload side-scan sonar imagery to run detection with the trained <strong style="color: var(--text-secondary);">best.onnx</strong> model.
          </p>
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="stage-btn" id="dashSampleShipwreck">Load Shipwreck</button>
          <button class="stage-btn" id="dashSampleDebris">Load Debris</button>
        </div>
      </div>

      <!-- Upload Dropzone & Action -->
      <div style="display: grid; grid-template-columns: 1fr auto; gap: 20px; align-items: stretch;">
        <div id="dashDropZone" style="border: 2px dashed var(--border-strong); border-radius: var(--radius-md); padding: 24px; text-align: left; cursor: pointer; background: rgba(0,0,0,0.2); display: flex; align-items: center; gap: 20px; transition: all 0.2s;">
          <input type="file" id="dashFileInput" accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff" style="display: none;" />
          <div style="width: 48px; height: 48px; border-radius: 50%; background: var(--color-bg-subtle); display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: inset 0 1px 1px rgba(255,255,255,0.05);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
            </svg>
          </div>
          <div>
            <div style="font-size: 15px; font-weight: 600; color: var(--text-primary); transition: color 0.2s;" id="dashUploadLabel">
              Choose sonar image or drag and drop here
            </div>
            <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
              Supports PNG, JPG, BMP · Physics-aware anomaly detection
            </div>
          </div>
        </div>

        <button class="btn btn-primary btn-lg" id="dashRunBtn" style="min-width: 220px; font-size: 16px;" ${isProcessing ? 'disabled' : ''}>
          ${isProcessing ? 'Analyzing...' : 'Run Detection →'}
        </button>
      </div>

      <div id="dashStatusMsg" style="margin-top: 16px; font-size: 13px; color: var(--color-primary); font-weight: 500; display: none; text-shadow: 0 0 8px rgba(6,182,212,0.3);"></div>
    </div>

    <!-- Results Section -->
    ${currentAnalysis ? `
      <!-- Useful Summary Metrics -->
      <div class="metric-grid">
        <div class="metric-card">
          <div class="metric-label">Objects Detected</div>
          <div class="metric-value" style="color: ${totalCount > 0 ? 'var(--color-primary)' : 'var(--text-muted)'}; text-shadow: ${totalCount > 0 ? 'var(--shadow-glow-cyan)' : 'none'};">
            ${totalCount}
          </div>
          <div class="metric-meta">${totalCount === 1 ? '1 target identified' : `${totalCount} targets identified`}</div>
        </div>

        <div class="metric-card">
          <div class="metric-label">Highest Confidence</div>
          <div class="metric-value" style="color: ${peakConf !== null && peakConf >= 80 ? 'var(--color-success)' : 'var(--text-primary)'}; text-shadow: ${peakConf !== null && peakConf >= 80 ? 'var(--shadow-glow-green)' : 'none'};">
            ${peakConf !== null ? `${peakConf.toFixed(1)}%` : 'N/A'}
          </div>
          <div class="metric-meta">Evaluation standard: YOLO</div>
        </div>

        <div class="metric-card">
          <div class="metric-label">Model Used</div>
          <div class="metric-value" style="font-size: 24px;">
            best.onnx
          </div>
          <div class="metric-meta">Latency: ${currentAnalysis.inference_seconds !== undefined ? `${currentAnalysis.inference_seconds}s` : '0.16s'}</div>
        </div>
      </div>

      <!-- Main Sonar Image Display & Detected Target List -->
      <div style="display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px;">
        <!-- Sonar Image with Bounding Boxes -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
              </svg>
              Inference Result
            </div>
            <span class="badge badge-cyan">Complete</span>
          </div>

          <div style="background: var(--color-bg-dark); border-radius: var(--radius-md); overflow: hidden; display: flex; align-items: center; justify-content: center; max-height: 460px; border: 1px solid var(--border-subtle); padding: 12px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);">
            <img src="${currentAnalysis.annotated_image_url || currentAnalysis.image_url}" alt="Annotated Sonar Image" style="max-width: 100%; max-height: 430px; object-fit: contain; filter: drop-shadow(0 0 8px rgba(255,255,255,0.1));" />
          </div>

          <div style="display: flex; gap: 12px; margin-top: 20px;">
            <button class="btn btn-primary" style="flex: 1;" id="dashGoResultsBtn">
              Interactive Viewer →
            </button>
            <button class="btn btn-secondary" id="dashGoMapBtn">
              Geospatial Map
            </button>
            <button class="btn btn-secondary" id="dashGoReportsBtn">
              Export CSV
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
              Physics-Aware Telemetry
            </div>
          </div>

          <div style="display: flex; flex-direction: column; gap: 12px; max-height: 440px; overflow-y: auto; padding-right: 8px;">
            ${detections.map(d => {
              const classType = (d.classification || 'other').toLowerCase();
              const revStatus = window.reviewStatusMap[d.id] || d.review_status || 'Unverified';
              const revBadgeClass = revStatus === 'Confirmed' ? 'badge-green' : (revStatus === 'Rejected' ? 'badge-red' : 'badge-amber');
              
              return `
                <div style="background: var(--color-bg-subtle); border: 1px solid var(--border-medium); border-left: 3px solid var(--color-class-${classType.includes('shipwreck') ? 'shipwreck' : 'other'}); border-radius: var(--radius-sm); padding: 16px;">
                  
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                      <div style="font-size: 13px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">${d.classification.toUpperCase()}</div>
                      <span id="badge-${d.id}" class="badge ${revBadgeClass}" style="font-size: 10px;">${revStatus}</span>
                    </div>
                    <span style="font-family: var(--font-mono); font-weight: 700; color: ${d.confidence >= 80 ? 'var(--color-success)' : 'var(--color-warning)'}; font-size: 14px; text-shadow: ${d.confidence >= 80 ? 'var(--shadow-glow-green)' : 'none'};">
                      YOLO: ${d.confidence.toFixed(1)}%
                    </span>
                  </div>
                  
                  <!-- Physics Verification Breakdown -->
                  <div style="font-size: 12px; color: var(--text-muted); display: flex; flex-direction: column; gap: 6px; font-family: var(--font-mono); background: rgba(0,0,0,0.2); padding: 10px; border-radius: var(--radius-sm); border: 1px solid rgba(255,255,255,0.05);">
                    <div style="display: flex; justify-content: space-between;">
                      <span>Acoustic Shadow:</span>
                      <span style="color: ${d.shadow_score > 30 ? 'var(--color-success)' : 'var(--color-warning)'};">${d.shadow_score ? d.shadow_score.toFixed(1) : 'N/A'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                      <span>Seabed Texture:</span>
                      <span style="color: var(--text-secondary);">${d.texture_score ? d.texture_score.toFixed(1) : 'N/A'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-weight: 700; color: var(--text-primary); border-top: 1px solid rgba(255,255,255,0.1); padding-top: 4px; margin-top: 2px;">
                      <span>Final Anomaly Score:</span>
                      <span style="color: ${d.anomaly_score >= 80 ? 'var(--color-success)' : 'var(--color-warning)'}; text-shadow: ${d.anomaly_score >= 80 ? 'var(--shadow-glow-green)' : 'none'};">${d.anomaly_score ? d.anomaly_score.toFixed(1) + '%' : 'N/A'}</span>
                    </div>
                  </div>

                  <!-- Physical & Geospatial -->
                  <div style="font-size: 12px; color: var(--text-secondary); display: flex; flex-direction: column; gap: 6px; font-family: var(--font-mono); margin-top: 12px;">
                    ${d.width_m && d.length_m ? `
                    <div style="display: flex; justify-content: space-between;">
                      <span>Dimensions (m):</span>
                      <span style="color: var(--text-primary);">${d.width_m}m × ${d.length_m}m</span>
                    </div>
                    ` : ''}
                    ${d.latitude !== null && d.latitude !== undefined ? `
                      <div style="display: flex; justify-content: space-between;">
                        <span>Coordinates:</span>
                        <span style="color: var(--text-accent);">${d.latitude.toFixed(6)}°, ${d.longitude.toFixed(6)}°</span>
                      </div>
                    ` : ''}
                  </div>
                  
                  <!-- Human-in-the-Loop Actions -->
                  <div id="btngrp-${d.id}" style="display: flex; gap: 8px; margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--border-strong);">
                    ${revStatus === 'Unverified' ? `
                        <button onclick="window.updateReviewStatus('${d.id}', 'Confirmed', 'btngrp-${d.id}', 'badge-${d.id}')" style="flex: 1; padding: 6px; font-size: 11px; font-weight: 600; border-radius: var(--radius-sm); border: 1px solid var(--color-success); background: var(--color-success-bg); color: var(--color-success); cursor: pointer; transition: all 0.2s;">
                          ✅ Confirm Object
                        </button>
                        <button onclick="window.updateReviewStatus('${d.id}', 'Rejected', 'btngrp-${d.id}', 'badge-${d.id}')" style="flex: 1; padding: 6px; font-size: 11px; font-weight: 600; border-radius: var(--radius-sm); border: 1px solid var(--color-danger); background: var(--color-danger-bg); color: var(--color-danger); cursor: pointer; transition: all 0.2s;">
                          ❌ False Positive
                        </button>
                    ` : `
                        <span style="color: var(--text-muted); font-size: 12px; font-weight: 500;">Reviewed by Operator</span>
                    `}
                  </div>
                </div>
              `;
            }).join('')}

            ${totalCount === 0 ? `
              <div style="text-align: center; padding: 60px 20px; color: var(--text-muted);">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--border-strong)" stroke-width="1" style="margin: 0 auto 16px;">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <div style="font-size: 15px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Clear Seafloor</div>
                <div style="font-size: 13px;">No anomalies detected above thresholds.</div>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    ` : `
      <!-- Clean Empty State Guide -->
      <div class="panel" style="text-align: center; padding: 80px 24px; color: var(--text-muted); background: linear-gradient(180deg, var(--color-bg-card) 0%, rgba(24,24,27,0.5) 100%); border: 1px dashed var(--border-medium);">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--border-strong)" stroke-width="1.5" style="margin: 0 auto 16px;">
          <rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
        </svg>
        <div style="font-size: 18px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px;">Awaiting Sonar Telemetry</div>
        <p style="font-size: 14px; max-width: 500px; margin: 0 auto; line-height: 1.6;">
          Upload a side-scan sonar image or select a sample to initialize the Physics-Aware Detection pipeline.
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

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--color-primary)';
    dropZone.style.background = 'var(--color-primary-bg)';
  });

  dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border-strong)';
    dropZone.style.background = 'rgba(0,0,0,0.2)';
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border-strong)';
    dropZone.style.background = 'rgba(0,0,0,0.2)';
    if (e.dataTransfer.files?.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files?.length > 0) {
      handleFileSelect(e.target.files[0]);
    }
  });

  function handleFileSelect(file) {
    selectedFile = file;
    selectedBlobUrl = null;
    selectedFilename = file.name;
    uploadLabel.textContent = file.name;
    uploadLabel.style.color = 'var(--color-primary)';
  }

  // Sample buttons
  container.querySelector('#dashSampleShipwreck')?.addEventListener('click', () => {
    selectedFile = null;
    selectedBlobUrl = '/samples/monrovia-side-scan-sonar-IVER-hires.png';
    selectedFilename = 'monrovia.png';
    uploadLabel.textContent = 'Sample: monrovia.png';
    uploadLabel.style.color = 'var(--color-primary)';
  });

  container.querySelector('#dashSampleDebris')?.addEventListener('click', () => {
    selectedFile = null;
    selectedBlobUrl = '/samples/sonar_test.jpg';
    selectedFilename = 'sonar_test.jpg';
    uploadLabel.textContent = 'Sample: sonar_test.jpg';
    uploadLabel.style.color = 'var(--color-primary)';
  });

  // Run AI Detection button
  runBtn.addEventListener('click', async () => {
    if (!selectedFile && !selectedBlobUrl) {
      selectedBlobUrl = '/samples/monrovia-side-scan-sonar-IVER-hires.png';
      selectedFilename = 'monrovia.png';
    }

    statusMsg.style.display = 'block';
    statusMsg.textContent = 'Running inference & acoustic validation...';
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
      alert(`Detection Error:\\n${err.message}`);
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
