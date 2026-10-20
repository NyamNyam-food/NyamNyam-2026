from django.test import TestCase
from django.contrib.auth.models import User
from app.models import Profile, Recipe, Restaurant
from app.logic import pagerank, rank_options

class RecommendationEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='taste_tester',password='long-password')
        self.profile = Profile.objects.create(user=self.user,flavors={'savory':8})

    def test_pagerank_scores_sum_to_one(self):
        scores=pagerank({'a':{'b':1},'b':{'a':1},'c':{}})
        self.assertAlmostEqual(sum(scores.values()),1,places=7)
        self.assertTrue(all(v>=0 for v in scores.values()))

    def test_unpriced_recipe_is_still_discoverable(self):
        Recipe.objects.create(author=self.user,title='Unpriced soup',ingredients=[{'name':'tomato','quantity':100,'unit':'g'}],cost_details={'complete':False},allergens=[],dietary=[])
        result=rank_options(self.profile,{'mode':'home','budget':20},Recipe.objects.all(),Restaurant.objects.all())
        self.assertEqual(len(result),1)
        self.assertIsNone(result[0]['price'])

    def test_allergy_filter_excludes_recipe(self):
        Recipe.objects.create(author=self.user,title='Peanut noodles',allergens=['Peanuts'],dietary=[])
        self.profile.allergies=['Peanuts'];self.profile.save()
        result=rank_options(self.profile,{'mode':'home'},Recipe.objects.all(),Restaurant.objects.all())
        self.assertEqual(result,[])

    def test_restaurant_without_menu_browsable_with_unknown_price(self):
        Restaurant.objects.create(owner=self.user,name='Cafe',address='Kaunas',latitude=54.9,longitude=23.9)
        result=rank_options(self.profile,{'mode':'restaurant'},Recipe.objects.all(),Restaurant.objects.all())
        self.assertEqual(len(result),1)
        self.assertIsNone(result[0]['price'])
