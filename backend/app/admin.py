from django.contrib import admin
from .models import Profile,Recipe,Restaurant,MenuItem,Review,ReviewFlag,Recommendation,ModerationLog,IngredientPrice
for model in [Profile,Recipe,Restaurant,MenuItem,Review,ReviewFlag,Recommendation,ModerationLog,IngredientPrice]:
 admin.site.register(model)
