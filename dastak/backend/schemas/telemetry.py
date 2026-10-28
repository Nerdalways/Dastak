import msgspec

class TelemetryPing(msgspec.Struct):
    v_id: str          # Vendor ID (e.g. "V-DEL-1049")
    lat: float         # Latitude
    lon: float         # Longitude
    acc: float         # Accuracy in meters
    ts: int            # Epoch timestamp