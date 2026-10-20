"""External OSM Nominatim geocoding and OSRM route distance.
Nominatim usage requires a meaningful User-Agent and low request volume.
"""
import requests
from .distance import distance_km

HEADERS = {'User-Agent': 'NyamNyamStudentProject/1.0 (educational restaurant finder; contact: project administrator)'}

def geocode_address(address):
    query = str(address).strip()
    if len(query) < 4:
        raise ValueError('Enter a complete street address.')
    response = requests.get('https://nominatim.openstreetmap.org/search', params={
        'q': query, 'format': 'jsonv2', 'addressdetails': 1, 'limit': 5,
        'countrycodes': 'lt', 'viewbox': '23.72,55.05,24.12,54.78',
    }, headers=HEADERS, timeout=8)
    response.raise_for_status()
    return [{'label': item['display_name'], 'lat': float(item['lat']), 'lon': float(item['lon'])}
            for item in response.json()]

def route_distance(origin_lat, origin_lon, target_lat, target_lon, mode='driving'):
    """OSRM driving route kilometres; no route is fabricated on failure."""
    if mode != 'driving':
        raise ValueError('Only driving distance is supported by this routing service.')
    straight = distance_km(origin_lat, origin_lon, target_lat, target_lon)
    url = (f'https://router.project-osrm.org/route/v1/driving/'
           f'{float(origin_lon)},{float(origin_lat)};{float(target_lon)},{float(target_lat)}')
    try:
        response = requests.get(url, params={'overview': 'false', 'steps': 'false'},
                                headers=HEADERS, timeout=8)
        response.raise_for_status()
        body = response.json()
        routes = body.get('routes') or []
        if body.get('code') == 'Ok' and routes:
            return {'distance_km': round(routes[0]['distance'] / 1000, 2),
                    'duration_minutes': round(routes[0]['duration'] / 60),
                    'distance_type': 'driving', 'provider': 'OSRM'}
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    return {'distance_km': straight, 'duration_minutes': None,
            'distance_type': 'straight_line_fallback', 'provider': 'Haversine'}
