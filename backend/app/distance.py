"""Straight-line distance between geographic coordinates in kilometres."""
from math import radians, sin, cos, sqrt, atan2

def distance_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    if not all((-90 <= x <= 90 for x in (lat1, lat2))) or not all((-180 <= x <= 180 for x in (lon1, lon2))):
        raise ValueError('Coordinates out of range')
    dlat = radians(lat2-lat1)
    dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return round(6371.0088 * 2 * atan2(sqrt(a), sqrt(max(0, 1-a))), 2)
