/**
 * MarineDebrisAI - Geotagging & Coordinate Service
 * Implements the mathematical models from geotag.py
 */

/**
 * Validate geographic coordinates and footprint bounds
 */
export function validateFootprint(latMin, latMax, lonMin, lonMax) {
  const minLat = parseFloat(latMin);
  const maxLat = parseFloat(latMax);
  const minLon = parseFloat(lonMin);
  const maxLon = parseFloat(lonMax);

  if (isNaN(minLat) || isNaN(maxLat) || isNaN(minLon) || isNaN(maxLon)) {
    return { valid: false, message: 'All footprint coordinates must be valid numbers.' };
  }

  if (minLat < -90 || minLat > 90 || maxLat < -90 || maxLat > 90) {
    return { valid: false, message: 'Latitude values must be between -90.0° and +90.0°.' };
  }

  if (minLon < -180 || minLon > 180 || maxLon < -180 || maxLon > 180) {
    return { valid: false, message: 'Longitude values must be between -180.0° and +180.0°.' };
  }

  if (minLat >= maxLat) {
    return { valid: false, message: 'Minimum latitude must be strictly less than maximum latitude.' };
  }

  if (minLon >= maxLon) {
    return { valid: false, message: 'Minimum longitude must be strictly less than maximum longitude.' };
  }

  return {
    valid: true,
    footprint: {
      latitude_min: minLat,
      latitude_max: maxLat,
      longitude_min: minLon,
      longitude_max: maxLon
    }
  };
}

/**
 * Convert pixel coordinates (X, Y) to estimated GPS (Lat, Lon)
 * Exactly mirrors footprint_pixel_to_gps from geotag.py:
 * Top -> latitude_max
 * Bottom -> latitude_min
 * Left -> longitude_min
 * Right -> longitude_max
 */
export function footprintPixelToGps(x, y, imageWidth, imageHeight, latMin, latMax, lonMin, lonMax) {
  const w = parseFloat(imageWidth);
  const h = parseFloat(imageHeight);
  if (w <= 0 || h <= 0) return { latitude: null, longitude: null };

  let xRatio = parseFloat(x) / w;
  let yRatio = parseFloat(y) / h;

  // Clamp normalized ratios [0, 1]
  xRatio = Math.max(0.0, Math.min(1.0, xRatio));
  yRatio = Math.max(0.0, Math.min(1.0, yRatio));

  const minLat = parseFloat(latMin);
  const maxLat = parseFloat(latMax);
  const minLon = parseFloat(lonMin);
  const maxLon = parseFloat(lonMax);

  const latitude = maxLat - (yRatio * (maxLat - minLat));
  const longitude = minLon + (xRatio * (maxLon - minLon));

  return {
    latitude: Number(latitude.toFixed(7)),
    longitude: Number(longitude.toFixed(7))
  };
}

/**
 * Format coordinates for tactical display
 */
export function formatCoordinates(lat, lon) {
  if (lat === null || lon === null || isNaN(lat) || isNaN(lon)) return 'N/A';
  const latDir = lat >= 0 ? 'N' : 'S';
  const lonDir = lon >= 0 ? 'E' : 'W';
  return `${Math.abs(lat).toFixed(6)}° ${latDir}, ${Math.abs(lon).toFixed(6)}° ${lonDir}`;
}
