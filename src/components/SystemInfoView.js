/**
 * MarineDebrisAI - System Specifications & Engineering Documentation View
 */

import { getCurrentMode, MODES, checkBackendHealth } from '../services/api.js';

export function renderSystemInfoView() {
  const container = document.createElement('div');
  container.className = 'system-info-view';

  const mode = getCurrentMode();
  const isDemo = mode === MODES.DEMO;

  container.innerHTML = `
    <!-- Top System Header -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;">
      <div>
        <h2 style="font-size: 20px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">System Architecture & AI Specifications</h2>
        <p style="font-size: 12px; color: var(--text-muted); font-family: var(--font-mono);">
          Deep-learning object detection pipeline & acoustic evidence scoring for side-scan sonar imagery.
        </p>
      </div>

      <div style="display: flex; align-items: center; gap: 10px;">
        <span class="badge ${isDemo ? 'badge-amber' : 'badge-green'}" style="font-size: 12px; padding: 6px 14px;">
          ${isDemo ? '● STANDALONE DEMO MODE' : '● LIVE PYTHON BACKEND MODE'}
        </span>
      </div>
    </div>

    <!-- 2-Column Grid of Technical Specifications -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
      
      <!-- Panel 1: Neural Network Specs -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="9"/>
              <path d="M12 2v20"/><path d="M2 12h20"/>
            </svg>
            YOLO11-Sonar Neural Network
          </div>
          <span class="badge badge-cyan">best.pt</span>
        </div>

        <div style="display: flex; flex-direction: column; gap: 12px; font-family: var(--font-mono); font-size: 12px;">
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">MODEL WEIGHTS:</span>
            <span style="color: var(--color-primary); font-weight: 700;">best.pt (6.25 MB)</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">BACKBONE:</span>
            <span>Ultralytics YOLO11 Nano / PyTorch 2.x</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">TRAINED CLASSES:</span>
            <span style="color: var(--color-success)">4 Target Categories</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">INFERENCE RESOLUTION:</span>
            <span>1024 × 1024 RGB Tensor</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">DEFAULT CONFIDENCE:</span>
            <span>0.25 (User Tunable: 0.10 - 0.95)</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">IOU SUPPRESSION:</span>
            <span>0.45 Non-Maximum Suppression</span>
          </div>
        </div>

        <!-- Target Classes Breakdown -->
        <div style="margin-top: 20px;">
          <div style="font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase; margin-bottom: 10px;">
            Trained Class Categories
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span class="badge class-shipwreck">0: SHIPWRECK</span>
            <span class="badge class-aircraft">1: AIRCRAFT</span>
            <span class="badge class-other">2: OTHER / DEBRIS</span>
            <span class="badge class-fish">3: FISH SCHOOL</span>
          </div>
        </div>
      </div>

      <!-- Panel 2: Preprocessing Pipeline Specs -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            Acoustic Preprocessing Pipeline
          </div>
          <span class="badge badge-cyan">preprocess.py</span>
        </div>

        <div style="display: flex; flex-direction: column; gap: 12px; font-family: var(--font-mono); font-size: 12px;">
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">NORMALIZATION:</span>
            <span>Aspect-preserved Lanczos to 1024×1024</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">CONTRAST ENHANCE:</span>
            <span>Adaptive stretch (factor 1.5)</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">NOISE REDUCTION:</span>
            <span>3×3 Median Filter (Preserves acoustic edges)</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">DROPOUT SCAN:</span>
            <span>32×32 pixel sliding uniform tile analysis</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            <span style="color: var(--text-muted)">QUALITY SCORE:</span>
            <span>0.35·Brightness + 0.40·Contrast + 0.25·Sharpness</span>
          </div>
        </div>
      </div>

    </div>

    <!-- Formula Breakdown Panel -->
    <div class="panel" style="margin-bottom: 24px;">
      <div class="panel-header">
        <div class="panel-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/>
          </svg>
          Multi-Factor Anomaly Scoring Model (sonar_analysis.py)
        </div>
        <span class="badge badge-green">MATHEMATICALLY FORMULATED</span>
      </div>

      <div style="background: rgba(6,11,17,0.7); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 16px; margin-bottom: 16px;">
        <div style="font-family: var(--font-mono); font-size: 14px; color: var(--color-primary); font-weight: 700; margin-bottom: 10px;">
          Anomaly Score = 0.70 × Model_Confidence + 0.12 × Shadow_Score + 0.08 × Quality_Score + 0.05 × Texture_Score + 0.05 × Edge_Score
        </div>
        <div style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.6;">
          • <strong>Model Confidence (70%):</strong> Primary detection certainty output by the trained YOLO11 neural weights.<br/>
          • <strong>Acoustic Shadow Evidence (12%):</strong> Ratio of down-range intensity drop immediately behind the detected target compared to background seabed backscatter.<br/>
          • <strong>Image Quality (8%):</strong> Global sharpness, contrast, and illumination sanity score.<br/>
          • <strong>Local Texture Score (5%):</strong> Local standard deviation in the region of interest.<br/>
          • <strong>Local Edge Score (5%):</strong> Canny edge response density around target perimeter.
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; font-family: var(--font-mono); font-size: 12px;">
        <div style="background: var(--color-bg-ocean); padding: 10px; border-radius: var(--radius-sm); border: 1px solid rgba(255, 59, 92, 0.3);">
          <strong style="color: #ff4757;">HIGH ANOMALY (≥ 80%)</strong>
          <p style="color: var(--text-muted); font-size: 11px; margin-top: 4px;">High confidence with corroborated acoustic shadow and structured boundaries.</p>
        </div>
        <div style="background: var(--color-bg-ocean); padding: 10px; border-radius: var(--radius-sm); border: 1px solid rgba(255, 176, 32, 0.3);">
          <strong style="color: #ffb020;">MODERATE ANOMALY (60 - 79%)</strong>
          <p style="color: var(--text-muted); font-size: 11px; margin-top: 4px;">Probable target or natural seafloor formation requiring secondary verification.</p>
        </div>
        <div style="background: var(--color-bg-ocean); padding: 10px; border-radius: var(--radius-sm); border: 1px solid rgba(0, 240, 255, 0.3);">
          <strong style="color: #00f0ff;">LOW ANOMALY (< 60%)</strong>
          <p style="color: var(--text-muted); font-size: 11px; margin-top: 4px;">Weak acoustic return or marginal shadow evidence; potential false positive.</p>
        </div>
      </div>
    </div>

    <!-- Python API Server Integration Guide -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>
          </svg>
          Python API Server Bridge (api_server.py)
        </div>
        <span class="badge ${isDemo ? 'badge-amber' : 'badge-green'}" id="backendHealthBadge">
          ${isDemo ? 'STANDALONE OFFLINE' : 'CONNECTED'}
        </span>
      </div>

      <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 14px; line-height: 1.5;">
        The frontend can run 100% offline in Standalone Demo Mode without external dependencies. To enable live inference directly using your GPU/CPU PyTorch environment:
      </p>

      <div style="background: #03070b; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 14px; font-family: var(--font-mono); font-size: 12px; color: var(--color-primary); margin-bottom: 14px;">
        # Start the Python REST API server in a separate terminal:<br/>
        <span style="color: #fff;">python api_server.py</span><br/><br/>
        # Server starts on: <span style="color: var(--color-success)">http://127.0.0.1:8000</span><br/>
        # Endpoints exposed:<br/>
        • GET  /api/health<br/>
        • POST /api/analyze<br/>
        • POST /api/report
      </div>

      <p style="font-size: 12px; color: var(--text-muted);">
        The original Streamlit application remains functional at any time: <code>streamlit run app.py</code>
      </p>
    </div>
  `;

  // Check health on load
  checkBackendHealth().then(res => {
    const badge = container.querySelector('#backendHealthBadge');
    if (badge && res.connected) {
      badge.textContent = 'BACKEND ONLINE (8000)';
      badge.className = 'badge badge-green';
    }
  });

  return container;
}
