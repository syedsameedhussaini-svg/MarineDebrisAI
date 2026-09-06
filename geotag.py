"""
MarineDebrisAI - Geotagging Utilities

Provides approximate geographic coordinates for detected objects
when real GPS/INS/sonar navigation metadata is not available.

NOTE:
These coordinates are estimates based on the geographic footprint
entered by the user. They are NOT real GPS measurements.
"""


def pixel_to_gps(
    x,
    y,
    image_width,
    image_height,
    survey_latitude,
    survey_longitude,
    latitude_span=0.01,
    longitude_span=0.01
):
    """
    Convert a pixel position into an estimated GPS coordinate.

    The center of the image corresponds approximately to the
    supplied survey reference coordinate.
    """

    if image_width <= 0 or image_height <= 0:
        return None, None

    x_ratio = x / image_width
    y_ratio = y / image_height

    latitude = (
        survey_latitude
        + (0.5 - y_ratio) * latitude_span
    )

    longitude = (
        survey_longitude
        + (x_ratio - 0.5) * longitude_span
    )

    return round(latitude, 7), round(longitude, 7)


def footprint_pixel_to_gps(
    x,
    y,
    image_width,
    image_height,
    latitude_min,
    latitude_max,
    longitude_min,
    longitude_max
):
    """
    Convert a pixel position into an estimated geographic
    coordinate using the geographic footprint of the image.

    Image convention:

        Top    -> latitude_max
        Bottom -> latitude_min
        Left   -> longitude_min
        Right  -> longitude_max
    """

    if image_width <= 0 or image_height <= 0:
        return None, None

    x_ratio = x / image_width
    y_ratio = y / image_height

    latitude = latitude_max - (
        y_ratio * (latitude_max - latitude_min)
    )

    longitude = longitude_min + (
        x_ratio * (longitude_max - longitude_min)
    )

    return round(latitude, 7), round(longitude, 7)


def valid_coordinate(latitude, longitude):
    """
    Check whether latitude and longitude are valid.
    """

    try:
        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError):
        return False

    return (
        -90.0 <= latitude <= 90.0
        and
        -180.0 <= longitude <= 180.0
    )


def normalize_number(value):
    """
    Safely convert a value to float.

    Returns None if conversion fails.
    """

    try:
        return float(value)

    except (TypeError, ValueError):
        return None