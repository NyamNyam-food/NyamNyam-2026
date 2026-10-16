from django.contrib import admin
from .models import Profile,Recipe,Restaurant,MenuItem,Review,Recommendation,ModerationLog,IngredientPrice,PantryItem
for model in [Profile,Recipe,Restaurant,MenuItem,Review,Recommendation,ModerationLog,IngredientPrice,PantryItem]:admin.site.register(model)
