from django.test import TestCase
from django.contrib.auth.models import User
from .models import Profile,Recipe
from .logic import taste_vector,rank_options
class RecommendationTests(TestCase):
 def setUp(self):
  self.u=User.objects.create_user('test',password='securepass123');self.p=Profile.objects.create(user=self.u,allergies=['Peanuts'])
 def test_normalized_vector(self):
  v=taste_vector({'sweet':5},20)
  self.assertAlmostEqual(sum(x*x for x in v),1,places=3)
 def test_allergen_exclusion(self):
  Recipe.objects.create(author=self.u,title='Unsafe',cost=10,allergens=['Peanuts'])
  Recipe.objects.create(author=self.u,title='Safe',cost=10)
  out=rank_options(self.p,{'mode':'home'},Recipe.objects.all(),[])
  self.assertEqual([x['title'] for x in out],['Safe'])
 def test_budget_exclusion(self):
  Recipe.objects.create(author=self.u,title='Expensive',cost=30)
  self.assertEqual(rank_options(self.p,{'mode':'home','budget':20},Recipe.objects.all(),[]),[])

from .logic import pagerank,haversine,estimate_cost,cosine
class AlgorithmTests(TestCase):
 def test_pagerank_normalization(self):
  graph={'a':{'b':1},'b':{'a':1,'c':1},'c':{'b':1}}
  result=pagerank(graph)
  self.assertAlmostEqual(sum(result.values()),1,places=7)
  self.assertGreater(result['b'],result['a'])
 def test_geographic_distance(self):
  self.assertAlmostEqual(haversine(54.9,23.9,54.9,23.9),0)
  self.assertGreater(haversine(54.9,23.9,55.0,23.9),10)
 def test_price_missing_is_reported(self):
  catalog={'rice':{'price':2,'unit':'kg'}}
  result=estimate_cost([{'name':'Rice','quantity':.5,'unit':'kg'},{'name':'Salt','quantity':1,'unit':'kg'}],catalog)
  self.assertEqual(result['estimated_cost'],1)
  self.assertFalse(result['complete'])
  self.assertEqual(result['missing_prices'],['Salt'])
 def test_cosine(self):
  self.assertAlmostEqual(cosine([1,0],[1,0]),1)
  self.assertAlmostEqual(cosine([1,0],[0,1]),0)
 def test_location_radius_exclusion(self):
  from .models import Restaurant,MenuItem
  owner=User.objects.create_user('owner_test',password='securepass123')
  r=Restaurant.objects.create(owner=owner,name='Far Away',address='Example',latitude=55.9,longitude=23.9)
  MenuItem.objects.create(restaurant=r,name='Soup',price=5)
  results=rank_options(self.p,{'mode':'restaurant','location':{'lat':54.9,'lon':23.9},'radius_km':10},[],[r])
  self.assertEqual(results,[])

from unittest.mock import Mock
from .ingredient_lookup import estimate_named_ingredients
class NamedIngredientQuoteTests(TestCase):
 def test_no_barcode_required_for_input(self):
  session=Mock()
  search=Mock();search.json.return_value={'products':[]};search.raise_for_status.return_value=None
  session.get.return_value=search
  quote=estimate_named_ingredients([{'name':'tomato','quantity':200,'unit':'g'}],session=session)
  self.assertFalse(quote['complete'])
  self.assertEqual(quote['estimated_cost'],'0.00')
  self.assertEqual(quote['missing_prices'][0]['name'],'tomato')
 def test_rejects_invalid_quantities(self):
  with self.assertRaises(ValueError):estimate_named_ingredients([{'name':'rice','quantity':-2,'unit':'kg'}])

class ReferenceEstimateTests(TestCase):
 def test_fallback_is_labeled_not_live(self):
  from .models import IngredientPrice
  from unittest.mock import Mock
  IngredientPrice.objects.create(name='tomato',unit='kg',price=3.20,source='ILLUSTRATIVE test estimate')
  session=Mock()
  response=Mock();response.json.return_value={'products':[]};response.raise_for_status.return_value=None
  session.get.return_value=response
  quote=estimate_named_ingredients([{'name':'tomato','quantity':200,'unit':'g'}],session=session)
  self.assertEqual(quote['estimated_cost'],'0.64')
  self.assertTrue(quote['complete'])
  self.assertEqual(quote['priced_ingredients'],[])
  self.assertEqual(quote['reference_estimates'][0]['source'],'ILLUSTRATIVE test estimate')
