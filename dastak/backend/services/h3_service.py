import h3

H3_RESOLUTION = 9

def get_h3_cell(lat: float, lon: float, resolution: int = H3_RESOLUTION) -> str:
    """Converts WGS84 coordinates into an H3 hexagonal cell index."""
    if hasattr(h3, "latlng_to_cell"):
        return h3.latlng_to_cell(lat, lon, resolution)
    return h3.geo_to_h3(lat, lon, resolution)