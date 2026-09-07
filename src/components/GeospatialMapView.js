/**
 * MarineDebrisAI - Geospatial Map View
 * Scientific GIS/map interface using standard OpenStreetMap (Free, No API Key Required)
 * Completely accurate: Never fabricates GPS data.
 */

import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { formatCoordinates } from '../services/geoService.js';

export function renderGeospatialMapView({ scanData }) {
  const container = document.createElement('div');
  container.className = 'map-view-container';

  const detections = (scanData?.detections || []).filter(d => d.latitude !== null && d.longitude !== null && !isNaN(d.latitude) && !isNaN(d.longitude));
  const hasGps = detections.length > 0;
  const footprint = scanData?.footprint;

  if (!hasGps) {
    container.innerHTML = `
      <div class="panel" style="text-align: center; padding: 60px 24px; max-width: 640px; margin: 40px auto;">
        <div style="width: 48px; height: 48px; border-radius: 50%; background: #fef3c7; border: 1px solid #fde68a; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
            <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" x2="9" y1="3" y2="18"/><line x1="15" x2="15" y1="6" y2="21"/>
          </svg>
        </div>
        <h2 style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px;">
          Geographic Coordinates Not Available
        </h2>
        <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 16px;">
          The current sonar scan was processed without geographic survey footprint metadata.
          <strong>MarineDebrisAI never fabricates GPS coordinates.</strong>
        </p>
        <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 20px;">
          To view target detections on the map, provide survey footprint coordinates (Min/Max Latitude & Longitude) in the <strong>Sonar Analysis</strong> view.
        </p>
      </div>
    `;
    return container;
  }

  // Calculate center of detections
  const centerLat = detections[0].latitude;
  const centerLon = detections[0].longitude;

  container.innerHTML = `
    <!-- Top Information Bar -->
    <div class="map-telemetry-bar">
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span style="font-weight: 600; color: var(--text-primary);">Detected Locations:</span>
        <span class="badge badge-green">${detections.length} Georeferenced</span>
        <span style="color: var(--text-muted);">Survey Scan:</span>
        <span style="font-weight: 600; color: var(--color-primary);">${scanData.filename || 'sonar_image.jpg'}</span>
      </div>
      <div style="font-size: 12px; color: var(--text-muted);">
        Map Provider: OpenStreetMap (No API Key Required)
      </div>
    </div>

    <!-- Scientific Map Canvas Card -->
    <div class="map-canvas-card">
      <div id="nauticalMap" style="width: 100%; height: 100%;"></div>
    </div>
  `;

  // Initialize standard Leaflet OpenStreetMap without watermark or external API key
  setTimeout(() => {
    const mapEl = container.querySelector('#nauticalMap');
    if (!mapEl) return;

    const map = L.map(mapEl, {
      center: [centerLat, centerLon],
      zoom: 15,
      zoomControl: true,
      attributionControl: true
    });

    // Standard OpenStreetMap tiles (natural, clean GIS cartography)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // If survey footprint rectangle exists, draw survey area bounds
    if (footprint && footprint.latitude_min !== undefined) {
      const bounds = [
        [footprint.latitude_min, footprint.longitude_min],
        [footprint.latitude_max, footprint.longitude_max]
      ];
      L.rectangle(bounds, {
        color: '#0f766e',
        weight: 2,
        dashArray: '6, 6',
        fillColor: '#0f766e',
        fillOpacity: 0.08
      }).addTo(map);
      map.fitBounds(bounds, { padding: [40, 40] });
    }

    // Add target markers
    detections.forEach(d => {
      const classType = (d.classification || 'other').toLowerCase();
      let markerColor = '#0f766e';
      if (classType === 'shipwreck') markerColor = '#b91c1c';
      else if (classType === 'aircraft') markerColor = '#c2410c';
      else if (classType === 'fish') markerColor = '#15803d';

      const customIcon = L.divIcon({
        className: 'sonar-marker-div',
        html: `
          <div style="width: 22px; height: 22px; border-radius: 50%; background: ${markerColor}; border: 2px solid #ffffff; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
            <div style="width: 6px; height: 6px; border-radius: 50%; background: #ffffff;"></div>
          </div>
        `,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });

      const marker = L.marker([d.latitude, d.longitude], { icon: customIcon }).addTo(map);

      marker.bindPopup(`
        <div style="font-family: var(--font-display); padding: 4px 6px;">
          <div style="font-weight: 700; color: ${markerColor}; font-size: 13px; margin-bottom: 6px;">
            ${d.classification.toUpperCase()} (${d.confidence.toFixed(1)}%)
          </div>
          <div style="font-size: 12px; color: #334155; line-height: 1.5;">
            <div><strong>ID:</strong> ${d.id}</div>
            <div><strong>Coordinates:</strong> ${formatCoordinates(d.latitude, d.longitude)}</div>
            ${d.anomaly_score !== null && d.anomaly_score !== undefined ? `<div><strong>Anomaly Score:</strong> ${d.anomaly_score.toFixed(1)}%</div>` : ''}
          </div>
        </div>
      `);
    });
  }, 100);

  return container;
}
