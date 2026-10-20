"""Import real mapped restaurants, with NO invented menus or ownership claims."""
import requests
import time
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from app.models import Profile,Restaurant

class Command(BaseCommand):
 help='Import OpenStreetMap restaurant listings in Kaunas (no menus; source: OSM contributors)'
 def add_arguments(self,parser):parser.add_argument('--limit',type=int,default=60)
 def handle(self,*args,**opts):
  # Named municipality area avoids relying on a guessed bounding box.
  query='[out:json][timeout:35];area["name"="Kaunas"]["boundary"="administrative"]->.a;(nwr["amenity"="restaurant"]["name"](area.a););out center tags 150;'
  endpoints = [
   'https://overpass.private.coffee/api/interpreter',
   'https://overpass.nchc.org.tw/api/interpreter',
   'https://overpass.kumi.systems/api/interpreter',
  ]
  elements = None
  errors = []
  headers = {'User-Agent': 'NyamNyamUniversityProject/1.0 (OSM data importer)', 'Accept': 'application/json'}
  for endpoint in endpoints:
   try:
    # POST query as raw Overpass QL; some mirrors reject form-encoded data.
    response = requests.post(endpoint, data=query.encode('utf-8'),
      headers={**headers, 'Content-Type': 'text/plain; charset=utf-8'}, timeout=60)
    if response.status_code in (400, 405, 406, 415):
     response = requests.get(endpoint, params={'data': query}, headers=headers, timeout=60)
    response.raise_for_status()
    elements = response.json()['elements']
    break
   except (requests.RequestException, KeyError, ValueError) as exc:
    errors.append(f'{endpoint}: {str(exc)[:180]}')
    time.sleep(2)
  if elements is None:
   raise CommandError('All Overpass mirrors failed. Try again later.\n' + '\n'.join(errors))
  importer,_=User.objects.get_or_create(username='osm_catalog',defaults={'is_active':False})
  Profile.objects.get_or_create(user=importer,defaults={'role':'owner'})
  count=0
  for el in elements:
   tags=el.get('tags',{});name=tags.get('name','').strip()
   loc=el.get('center',el);lat=loc.get('lat');lon=loc.get('lon')
   if not name or lat is None or lon is None:continue
   address=', '.join(filter(None,[tags.get('addr:street'),tags.get('addr:housenumber'),tags.get('addr:city','Kaunas')]))
   osm_key=f"OSM {el['type']}/{el['id']}"
   if Restaurant.objects.filter(description__contains=osm_key).exists():continue
   Restaurant.objects.create(owner=importer,name=name,address=address or 'Kaunas, Lithuania',latitude=lat,longitude=lon,
    cuisine=tags.get('cuisine','Restaurant')[:80],description=f'Community-mapped listing · {osm_key}. Menu and prices have not been verified.')
   count+=1
   if count>=opts['limit']:break
  self.stdout.write(self.style.SUCCESS(f'Imported {count} OSM restaurants. No fabricated menus. © OpenStreetMap contributors (ODbL).'))
