from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .distance import distance_km
from .models import Restaurant

class DistanceTests(SimpleTestCase):
    def test_same_point(self):
        self.assertEqual(distance_km(54.9, 23.9, 54.9, 23.9), 0)
    def test_one_degree_equator(self):
        self.assertAlmostEqual(distance_km(0, 0, 0, 1), 111.20, delta=.1)
    def test_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            distance_km(100, 0, 0, 0)

class NearbyRestaurantTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user('test_owner', password='test-pass-123')
        Restaurant.objects.create(owner=owner, name='Near', address='Test', latitude=54.9, longitude=23.9)
        Restaurant.objects.create(owner=owner, name='Far', address='Test', latitude=55.5, longitude=24.5)
        self.client = APIClient()
    def test_filters_and_sorts(self):
        r = self.client.get('/api/restaurants/nearby/', {'lat':54.9, 'lon':23.9, 'radius':10})
        self.assertEqual(r.status_code, 200)
        self.assertEqual([x['name'] for x in r.data], ['Near'])
        self.assertEqual(r.data[0]['distance_km'], 0)
    def test_invalid_query(self):
        self.assertEqual(self.client.get('/api/restaurants/nearby/', {'lat':999,'lon':1}).status_code, 400)
