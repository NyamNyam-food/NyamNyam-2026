from django.db import models
from django.contrib.auth.models import User
class Profile(models.Model):
 user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
 role=models.CharField(max_length=12,choices=[('customer','Customer'),('owner','Restaurant Owner')],default='customer')
 dietary=models.JSONField(default=list);allergies=models.JSONField(default=list);flavors=models.JSONField(default=dict);taste_vector=models.JSONField(default=list)
 cuisine=models.CharField(max_length=80,blank=True)
 def __str__(self):return self.user.username
class Recipe(models.Model):
 author=models.ForeignKey(User,on_delete=models.CASCADE,related_name='recipes')
 title=models.CharField(max_length=160);description=models.TextField(blank=True);cuisine=models.CharField(max_length=80,default='International')
 ingredients=models.JSONField(default=list);steps=models.JSONField(default=list);allergens=models.JSONField(default=list);dietary=models.JSONField(default=list)
 minutes=models.PositiveIntegerField(default=25);cost=models.DecimalField(max_digits=8,decimal_places=2,default=0)
 mood=models.JSONField(default=list,blank=True);image=models.URLField(blank=True);cost_details=models.JSONField(default=dict,blank=True);created=models.DateTimeField(auto_now_add=True)
class Restaurant(models.Model):
 owner=models.ForeignKey(User,on_delete=models.CASCADE,related_name='restaurants')
 name=models.CharField(max_length=160);description=models.TextField(blank=True);address=models.CharField(max_length=255)
 latitude=models.FloatField(null=True,blank=True);longitude=models.FloatField(null=True,blank=True)
 cuisine=models.CharField(max_length=80,default='International');image=models.URLField(blank=True)
class MenuItem(models.Model):
 restaurant=models.ForeignKey(Restaurant,on_delete=models.CASCADE,related_name='menu')
 name=models.CharField(max_length=160);description=models.TextField(blank=True);price=models.DecimalField(max_digits=8,decimal_places=2)
 allergens=models.JSONField(default=list);dietary=models.JSONField(default=list);image=models.URLField(blank=True)
class Review(models.Model):
 author=models.ForeignKey(User,on_delete=models.CASCADE)
 recipe=models.ForeignKey(Recipe,on_delete=models.CASCADE,null=True,blank=True,related_name='reviews')
 restaurant=models.ForeignKey(Restaurant,on_delete=models.CASCADE,null=True,blank=True,related_name='reviews')
 rating=models.PositiveSmallIntegerField();comment=models.TextField(blank=True);is_visible=models.BooleanField(default=True);created=models.DateTimeField(auto_now_add=True)
class Recommendation(models.Model):
 user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='history');filters=models.JSONField(default=dict);results=models.JSONField(default=list);created=models.DateTimeField(auto_now_add=True)
class ReviewFlag(models.Model):
 reporter=models.ForeignKey(User,on_delete=models.CASCADE)
 review=models.ForeignKey(Review,on_delete=models.CASCADE,related_name='flags')
 reason=models.CharField(max_length=300)
 resolved=models.BooleanField(default=False)
 created=models.DateTimeField(auto_now_add=True)
 class Meta:
  constraints=[models.UniqueConstraint(fields=['reporter','review'],name='one_flag_per_review_reporter')]

class ModerationLog(models.Model):
 admin=models.ForeignKey(User,on_delete=models.SET_NULL,null=True);action=models.CharField(max_length=120);target=models.CharField(max_length=200);created=models.DateTimeField(auto_now_add=True)

class IngredientPrice(models.Model):
 name=models.CharField(max_length=120,unique=True)
 unit=models.CharField(max_length=24,default='kg')
 price=models.DecimalField(max_digits=9,decimal_places=2)
 source=models.CharField(max_length=255,default='Manual reference catalog')
 updated=models.DateTimeField(auto_now=True)
