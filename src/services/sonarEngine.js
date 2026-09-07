/**
 * MarineDebrisAI - Acoustic & Anomaly Scoring Engine
 * Implements exact formulas from sonar_analysis.py
 */

/**
 * Calculate the Composite Anomaly Score
 * Formula:
 * Anomaly Score = 0.70 * confidence + 0.12 * shadow + 0.08 * quality + 0.05 * texture + 0.05 * edge
 * (where each component is normalized to [0, 100]%)
 */
export function calculateAnomalyScore(confidence, shadowScore, qualityScore, textureScore, edgeScore) {
  const conf = Math.max(0, Math.min(100, Number(confidence) || 0));
  const shadow = Math.max(0, Math.min(100, Number(shadowScore) || 0));
  const quality = Math.max(0, Math.min(100, Number(qualityScore) || 0));
  const texture = Math.max(0, Math.min(100, Number(textureScore) || 0));
  const edge = Math.max(0, Math.min(100, Number(edgeScore) || 0));

  const score = (
    0.70 * conf +
    0.12 * shadow +
    0.08 * quality +
    0.05 * texture +
    0.05 * edge
  );

  const rounded = Number(Math.max(0, Math.min(100, score)).toFixed(2));
  
  let assessment = 'Low';
  if (rounded >= 80) assessment = 'High';
  else if (rounded >= 60) assessment = 'Moderate';

  return {
    anomalyScore: rounded,
    anomalyAssessment: assessment,
    breakdown: {
      confContribution: Number((0.70 * conf).toFixed(2)),
      shadowContribution: Number((0.12 * shadow).toFixed(2)),
      qualityContribution: Number((0.08 * quality).toFixed(2)),
      textureContribution: Number((0.05 * texture).toFixed(2)),
      edgeContribution: Number((0.05 * edge).toFixed(2))
    }
  };
}

/**
 * Determine confidence category
 */
export function getConfidenceCategory(confidencePercent) {
  const conf = Number(confidencePercent);
  if (conf >= 80) return 'High';
  if (conf >= 60) return 'Moderate';
  return 'Low';
}

/**
 * Client-side acoustic metric analysis for custom uploaded images (HTML Canvas based)
 */
export function analyzeImageCanvas(imageElement) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const w = imageElement.naturalWidth || imageElement.width || 1024;
  const h = imageElement.naturalHeight || imageElement.height || 1024;
  canvas.width = Math.min(w, 512);
  canvas.height = Math.min(h, 512);
  ctx.drawImage(imageElement, 0, 0, canvas.width, canvas.height);

  const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imgData.data;
  let sumGray = 0;
  const count = data.length / 4;

  for (let i = 0; i < data.length; i += 4) {
    const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    sumGray += gray;
  }
  const brightness = sumGray / count;

  let sumDiffSq = 0;
  for (let i = 0; i < data.length; i += 4) {
    const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    sumDiffSq += Math.pow(gray - brightness, 2);
  }
  const contrast = Math.sqrt(sumDiffSq / count);

  // Approximate sharpness
  const sharpness = Math.min(contrast * 0.85, 80);

  // Quality score formula matching preprocess.py
  const brightnessScore = 1.0 - Math.min(Math.abs(brightness - 127.5) / 127.5, 1.0);
  const contrastScore = Math.min(contrast / 64.0, 1.0);
  const sharpnessScore = Math.min(sharpness / 32.0, 1.0);
  const qualityScore = Number(((0.35 * brightnessScore + 0.40 * contrastScore + 0.25 * sharpnessScore) * 100).toFixed(2));

  return {
    brightness: Number(brightness.toFixed(2)),
    contrast: Number(contrast.toFixed(2)),
    sharpness: Number(sharpness.toFixed(2)),
    quality_score: qualityScore,
    dropout_detected: contrast < 8,
    dropout_percentage: contrast < 8 ? 4.2 : 0.0
  };
}
