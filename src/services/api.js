/**
 * MarineDebrisAI - Python Backend API Service
 * Connects directly to FastAPI backend (api_server.py)
 * Runs real YOLO best.pt inference and real preprocessing.
 * Zero fabricated or mock detections.
 */

import { validateFootprint } from './geoService.js';

// Environment-aware API base URL (empty for same-origin / Vercel relative path or local Vite proxy)
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export function getApiUrl(endpoint) {
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

let isBackendAvailable = false;

/**
 * Check backend connection status
 */
export async function checkBackendHealth(timeoutMs = 15000) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    const url = getApiUrl('/api/health');
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (response.ok) {
      const data = await response.json();
      isBackendAvailable = true;
      return { connected: true, data };
    }
  } catch (err) {
    // Backend offline
  }
  isBackendAvailable = false;
  const targetDesc = API_BASE_URL ? API_BASE_URL : 'local port 8000';
  return {
    connected: false,
    message: `AI OFFLINE: Python backend is not responding at ${targetDesc}. (If using Render free tier, it may take 30-45s to spin up from sleep).`
  };
}

export function getBackendStatus() {
  return isBackendAvailable;
}

/**
 * Send real sonar image to FastAPI backend for real YOLO best.pt inference
 */
export async function runRealSonarAnalysis({
  imageFile,
  imageBlob,
  filename = 'sonar_image.jpg',
  footprint = null,
  confidenceThreshold = 0.25,
  iouThreshold = 0.45,
  onProgress = () => {}
}) {
  onProgress(10, 'Connecting to FastAPI backend...');
  let health = await checkBackendHealth(12000);
  if (!health.connected) {
    onProgress(15, 'Backend waking up from sleep, retrying in 3s...');
    await new Promise(r => setTimeout(r, 3000));
    health = await checkBackendHealth(12000);
  }
  if (!health.connected) {
    const targetDesc = API_BASE_URL ? API_BASE_URL : 'http://127.0.0.1:8000';
    throw new Error(`AI OFFLINE: The Python backend service is not responding at ${targetDesc}. Render free tier takes ~30-45s to wake up if inactive. Tap the status pill to reconnect once awake.`);
  }

  onProgress(25, 'Uploading sonar image...');
  const formData = new FormData();
  if (imageFile) {
    formData.append('image', imageFile, imageFile.name);
  } else if (imageBlob) {
    formData.append('image', imageBlob, filename);
  } else {
    throw new Error('Please select or upload a sonar image.');
  }

  // Footprint coordinates are optional
  if (footprint && footprint.latitude_min !== undefined && footprint.latitude_min !== '') {
    const fpVal = validateFootprint(
      footprint.latitude_min,
      footprint.latitude_max,
      footprint.longitude_min,
      footprint.longitude_max
    );
    if (fpVal.valid) {
      formData.append('latitude_min', String(footprint.latitude_min));
      formData.append('latitude_max', String(footprint.latitude_max));
      formData.append('longitude_min', String(footprint.longitude_min));
      formData.append('longitude_max', String(footprint.longitude_max));
    }
  }

  formData.append('conf', String(confidenceThreshold));
  formData.append('iou', String(iouThreshold));

  onProgress(50, 'Running YOLO best.pt inference on Python backend...');
  const analyzeUrl = getApiUrl('/api/analyze');
  const response = await fetch(analyzeUrl, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const errText = await response.text();
    let detail = errText;
    try {
      const errJson = JSON.parse(errText);
      detail = errJson.detail || errJson.error || errText;
    } catch {}
    throw new Error(`Inference error: ${detail}`);
  }

  onProgress(85, 'Receiving actual detections and bounding boxes...');
  const result = await response.json();

  onProgress(100, 'Detection complete.');
  return result;
}
