/**
 * MarineDebrisAI - Report Exporter Service
 * Generates JSON and CSV anomaly reports matching report.py & app.py schemas
 */

/**
 * Generate and trigger download of the structured JSON report
 */
export function downloadJsonReport(scanData, filename = 'detection_report.json') {
  const reportPayload = {
    project: 'MarineDebrisAI',
    timestamp: new Date().toISOString(),
    image: scanData.image || 'sonar_scan.jpg',
    image_dimensions: scanData.image_dimensions || { width: 1024, height: 1024 },
    survey_footprint: scanData.footprint || {
      latitude_min: 0,
      latitude_max: 0,
      longitude_min: 0,
      longitude_max: 0
    },
    processing: {
      processing_resolution: '1024x1024',
      image_quality: scanData.quality || { quality_score: 0 },
      dropout_analysis: scanData.dropout_analysis || { dropout_detected: false, dropout_percentage: 0 },
      total_processing_seconds: scanData.total_processing_time || 0.42,
      yolo_inference_seconds: scanData.yolo_inference_time || 0.08,
      model: 'best.pt (YOLO11-Sonar)'
    },
    detections: scanData.detections || [],
    limitations: [
      'Geographic coordinates are approximate and derived from the supplied image footprint.',
      'Actual GPS/INS/sonar navigation metadata was not available.',
      'True heave, pitch and roll correction is therefore not performed.',
      'Dropout detection is image-based and does not represent definitive sonar acquisition-data loss detection.'
    ]
  };

  const jsonBlob = new Blob([JSON.stringify(reportPayload, null, 2)], { type: 'application/json' });
  triggerFileDownload(jsonBlob, filename);
}

/**
 * Generate and trigger download of the CSV report matching report.py
 */
export function downloadCsvReport(scanData, filename = 'anomaly_report.csv') {
  const detections = scanData.detections || [];
  
  const headers = [
    'image',
    'id',
    'classification',
    'review_status',
    'confidence_percent',
    'confidence_level',
    'anomaly_score_percent',
    'anomaly_assessment',
    'shadow_score',
    'texture_score',
    'center_x',
    'center_y',
    'x1',
    'y1',
    'x2',
    'y2',
    'width_pixels',
    'height_pixels',
    'width_meters',
    'length_meters',
    'latitude',
    'longitude'
  ];

  const rows = detections.map(d => {
    const box = d.bounding_box || { x1: 0, y1: 0, x2: 0, y2: 0 };
    const center = d.center_pixel || { x: 0, y: 0 };
    const revStatus = window.reviewStatusMap ? (window.reviewStatusMap[d.id] || d.review_status || 'Unverified') : (d.review_status || 'Unverified');
    return [
      escapeCsv(d.image || scanData.image || 'sonar_scan.jpg'),
      escapeCsv(d.id || ''),
      escapeCsv(d.classification || 'unknown'),
      escapeCsv(revStatus),
      d.confidence !== undefined ? Number(d.confidence).toFixed(2) : '0.00',
      escapeCsv(d.confidence_level || 'Moderate'),
      d.anomaly_score !== undefined ? Number(d.anomaly_score).toFixed(2) : '0.00',
      escapeCsv(d.anomaly_assessment || 'Moderate'),
      d.shadow_score !== undefined ? Number(d.shadow_score).toFixed(2) : '0.00',
      d.texture_score !== undefined ? Number(d.texture_score).toFixed(2) : '0.00',
      Number(center.x).toFixed(2),
      Number(center.y).toFixed(2),
      Number(box.x1).toFixed(2),
      Number(box.y1).toFixed(2),
      Number(box.x2).toFixed(2),
      Number(box.y2).toFixed(2),
      Number(d.width_pixels || (box.x2 - box.x1)).toFixed(2),
      Number(d.height_pixels || (box.y2 - box.y1)).toFixed(2),
      d.width_m !== undefined ? Number(d.width_m).toFixed(2) : '',
      d.length_m !== undefined ? Number(d.length_m).toFixed(2) : '',
      d.latitude !== null && d.latitude !== undefined ? Number(d.latitude).toFixed(7) : '',
      d.longitude !== null && d.longitude !== undefined ? Number(d.longitude).toFixed(7) : ''
    ].join(',');
  });

  const csvContent = [headers.join(','), ...rows].join('\r\n');
  const csvBlob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  triggerFileDownload(csvBlob, filename);
}

function escapeCsv(str) {
  if (str === null || str === undefined) return '""';
  const val = String(str).replace(/"/g, '""');
  return `"${val}"`;
}

function triggerFileDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
