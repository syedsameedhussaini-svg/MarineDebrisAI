"""
MarineDebrisAI - Geotagging Utilities

Provides approximate pixel-to-geographic coordinate conversion
using a geographic footprint supplied for the sonar image.

For accurate marine positioning, real GPS/INS/sonar navigation
metadata should be used.
"""


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
    Convert an image pixel coordinate to an estimated
    geographic coordinate.

    Image convention:

        top    -> latitude_max
        bottom -> latitude_min
        left   -> longitude_min
        right  -> longitude_max

    Parameters
    ----------
    x : float
        Pixel X coordinate.

    y : float
        Pixel Y coordinate.

    image_width : int
        Image width in pixels.

    image_height : int
        Image height in pixels.

    latitude_min : float
        Minimum latitude of survey footprint.

    latitude_max : float
        Maximum latitude of survey footprint.

    longitude_min : float
        Minimum longitude of survey footprint.

    longitude_max : float
        Maximum longitude of survey footprint.

    Returns
    -------
    tuple
        (latitude, longitude)
    """

    try:

        image_width = float(
            image_width
        )

        image_height = float(
            image_height
        )

        x = float(x)
        y = float(y)

        latitude_min = float(
            latitude_min
        )

        latitude_max = float(
            latitude_max
        )

        longitude_min = float(
            longitude_min
        )

        longitude_max = float(
            longitude_max
        )

    except (
        TypeError,
        ValueError
    ):

        return None, None


    if (
        image_width <= 0
        or image_height <= 0
    ):

        return None, None


    # Normalize pixel position.

    x_ratio = (
        x / image_width
    )

    y_ratio = (
        y / image_height
    )


    # Clamp normalized values.

    x_ratio = max(
        0.0,
        min(
            1.0,
            x_ratio
        )
    )

    y_ratio = max(
        0.0,
        min(
            1.0,
            y_ratio
        )
    )


    # Convert to geographic coordinates.

    latitude = (
        latitude_max
        - (
            y_ratio
            * (
                latitude_max
                - latitude_min
            )
        )
    )


    longitude = (
        longitude_min
        + (
            x_ratio
            * (
                longitude_max
                - longitude_min
            )
        )
    )


    return (
        round(latitude, 7),
        round(longitude, 7)
    )


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
    Convert a pixel coordinate into an approximate GPS
    coordinate using a central survey reference point.
    """

    try:

        image_width = float(
            image_width
        )

        image_height = float(
            image_height
        )

        x = float(x)
        y = float(y)

        survey_latitude = float(
            survey_latitude
        )

        survey_longitude = float(
            survey_longitude
        )

        latitude_span = float(
            latitude_span
        )

        longitude_span = float(
            longitude_span
        )

    except (
        TypeError,
        ValueError
    ):

        return None, None


    if (
        image_width <= 0
        or image_height <= 0
    ):

        return None, None


    x_ratio = (
        x / image_width
    )

    y_ratio = (
        y / image_height
    )


    latitude = (
        survey_latitude
        + (
            0.5 - y_ratio
        )
        * latitude_span
    )


    longitude = (
        survey_longitude
        + (
            x_ratio - 0.5
        )
        * longitude_span
    )


    return (
        round(latitude, 7),
        round(longitude, 7)
    )


def valid_coordinate(
    latitude,
    longitude
):
    """
    Check whether latitude and longitude
    are valid geographic values.
    """

    try:

        latitude = float(
            latitude
        )

        longitude = float(
            longitude
        )

    except (
        TypeError,
        ValueError
    ):

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

    except (
        TypeError,
        ValueError
    ):

        return None
def pixel_to_meters(w_px, h_px, image_width, image_height, swath_width_m=100.0, along_track_m=150.0):
    """
    Convert bounding box pixel dimensions to physical meters.
    Assumes a default Side-Scan Sonar geometry (e.g., 50m port, 50m starboard).
    """
    try:
        w_ratio = float(w_px) / float(image_width)
        h_ratio = float(h_px) / float(image_height)
        
        width_m = w_ratio * float(swath_width_m)
        height_m = h_ratio * float(along_track_m)
        
        return round(width_m, 2), round(height_m, 2)
    except Exception:
        return None, None
