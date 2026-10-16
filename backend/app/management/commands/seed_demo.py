from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Profile,Recipe,Restaurant,MenuItem,IngredientPrice
from app.logic import taste_vector
class Command(BaseCommand):
 help='Populate demo data (idempotent)'
 def handle(self,*args,**kwargs):
  u,_=User.objects.get_or_create(username='demo',defaults={'email':'demo@example.com'});u.set_password('DemoPass123!');u.save()
  p,_=Profile.objects.get_or_create(user=u);p.taste_vector=taste_vector({'savory':4},25);p.save()
  owner,_=User.objects.get_or_create(username='owner',defaults={'email':'owner@example.com'});owner.set_password('OwnerPass123!');owner.save()
  op,_=Profile.objects.get_or_create(user=owner);op.role='owner';op.save()
  recipes=[('Creamy Tomato Pasta','Italian',12,25,['Tomatoes','Pasta','Garlic','Olive oil'],['Boil pasta until tender','Simmer tomatoes with garlic','Toss and serve'],['Wheat']),('Rainbow Buddha Bowl','Healthy',9,20,['Rice','Avocado','Carrots','Chickpeas'],['Cook the rice','Chop vegetables','Arrange and serve'],[]),('Spicy Chickpea Curry','Indian',8,35,['Chickpeas','Tomatoes','Coconut milk','Curry powder'],['Sauté spices','Add chickpeas and tomatoes','Simmer until rich'],[]),('Mediterranean Salad','Mediterranean',7,15,['Cucumber','Tomato','Olives','Lemon'],['Chop vegetables','Mix with lemon dressing','Serve chilled'],[])]
  for name,cuisine,cost,minutes,ingredients,steps,allergens in recipes:
   Recipe.objects.get_or_create(title=name,author=u,defaults={'description':'Fresh, comforting and full of flavor.','cuisine':cuisine,'cost':cost,'minutes':minutes,'ingredients':ingredients,'steps':steps,'allergens':allergens,'dietary':['Vegetarian']})
  # Illustrative prices only. These are not live supermarket quotes; administrators may edit them.
  reference={'tomato':(3.20,'kg'),'tomatoes':(3.20,'kg'),'garlic':(7.00,'kg'),
   'potato':(1.60,'kg'),'potatoes':(1.60,'kg'),'water':(0.01,'l'),
   'rice':(2.50,'kg'),'pasta':(2.40,'kg'),'onion':(1.50,'kg'),
   'carrot':(1.40,'kg'),'carrots':(1.40,'kg'),'milk':(1.60,'l'),
   'flour':(1.30,'kg'),'egg':(0.30,'piece'),'eggs':(0.30,'piece'),
   'olive oil':(9.00,'l'),'salt':(0.80,'kg'),'sugar':(1.20,'kg'),
   'chicken':(8.50,'kg'),'cheese':(9.00,'kg'),'bread':(3.00,'kg'),
   'cucumber':(2.20,'kg'),'chickpeas':(3.00,'kg'),'lemon':(0.60,'piece'),
   'butter':(9.00,'kg'),'avocado':(1.30,'piece'),'coconut milk':(4.00,'l')}
  for name,(price,unit) in reference.items():
   IngredientPrice.objects.update_or_create(name=name,defaults={'price':price,'unit':unit,
     'source':'ILLUSTRATIVE coursework estimate, NOT a live store price'})
  # Real restaurant names are imported from OpenStreetMap separately; no fabricated real menus.

  self.stdout.write(self.style.SUCCESS('Demo data ready. Customer demo / DemoPass123!; owner / OwnerPass123!'))
