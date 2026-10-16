from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Profile,Recipe,Restaurant,MenuItem,Review,Recommendation,ModerationLog,PantryItem,IngredientPrice
from .logic import taste_vector,rank_options,estimate_cost
import requests

def fail(msg,code=400):return Response({'error':msg},status=code)
def me(u):
 p,_=Profile.objects.get_or_create(user=u)
 return {'id':u.id,'username':u.username,'email':u.email,'role':'admin' if u.is_staff else p.role,'profile':{'dietary':p.dietary,'allergies':p.allergies,'flavors':p.flavors,'taste_vector':p.taste_vector,'budget':p.budget,'cuisine':p.cuisine}}
def recipe_data(r):return {'id':r.id,'author':r.author.username,'title':r.title,'description':r.description,'cuisine':r.cuisine,'ingredients':r.ingredients,'steps':r.steps,'allergens':r.allergens,'dietary':r.dietary,'minutes':r.minutes,'cost':float(r.cost) if r.cost_details.get('complete') else None,'cost_details':r.cost_details,'image':r.image,'rating':round(r.reviews.aggregate(v=Avg('rating'))['v'] or 0,1)}
def restaurant_data(r):return {'id':r.id,'owner':r.owner.username,'name':r.name,'description':r.description,'address':r.address,'latitude':r.latitude,'longitude':r.longitude,'cuisine':r.cuisine,'image':r.image,'rating':round(r.reviews.aggregate(v=Avg('rating'))['v'] or 0,1),'menu':[{'id':m.id,'name':m.name,'description':m.description,'price':float(m.price),'allergens':m.allergens,'dietary':m.dietary,'image':m.image} for m in r.menu.all()]}
def review_data(r):return {'id':r.id,'author':r.author.username,'rating':r.rating,'comment':r.comment,'recipe':r.recipe_id,'restaurant':r.restaurant_id,'created':r.created.isoformat()}
def can_edit(user,obj):return user.is_staff or obj.author_id==user.id if isinstance(obj,(Recipe,Review)) else user.is_staff or obj.owner_id==user.id
@api_view(['GET'])
@permission_classes([AllowAny])
def csrf(request):return Response({'csrfToken':get_token(request)})
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
 d=request.data;email=str(d.get('email','')).strip().lower();username=str(d.get('username','')).strip();password=d.get('password','')
 if not username or not email or len(password)<8:return fail('Username, email and password (8+ characters) are required.')
 if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=username).exists():return fail('Email or username already registered.')
 role=d.get('role','customer')
 if role not in ['customer','owner']:return fail('Invalid role.')
 try:
  with transaction.atomic():
   u=User.objects.create_user(username=username,email=email,password=password)
   p=Profile.objects.create(user=u,role=role)
   if role=='customer':update_profile(p,d.get('profile',{}))
  login(request,u);return Response(me(u),status=201)
 except (ValueError,TypeError) as e:return fail(str(e))
@api_view(['POST'])
@permission_classes([AllowAny])
def sign_in(request):
 d=request.data;u=authenticate(request,username=d.get('username',''),password=d.get('password',''))
 if not u:return fail('Invalid username or password.',401)
 login(request,u);return Response(me(u))
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sign_out(request):logout(request);return Response({'ok':True})
@api_view(['GET','PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def account(request):
 if request.method=='DELETE':
  request.user.delete();logout(request);return Response({'ok':True})
 if request.method=='PATCH':
  if request.user.is_staff or request.user.profile.role!='customer':return fail('Taste survey is available to customers only.',403)
  try:update_profile(request.user.profile,request.data)
  except (ValueError,TypeError) as e:return fail(str(e))
 return Response(me(request.user))
def update_profile(p,d):
 for key in ['dietary','allergies']:
  if key in d:
   if not isinstance(d[key],list):raise ValueError(key+' must be a list')
   setattr(p,key,[str(x) for x in d[key]])
 if 'flavors' in d:
  if not isinstance(d['flavors'],dict):raise ValueError('Invalid flavor values')
  p.flavors=d['flavors']
 if 'budget' in d:
  budget=int(d['budget'])
  if not 1<=budget<=200:raise ValueError('Budget must be between 1 and 200')
  p.budget=budget
 if 'cuisine' in d:p.cuisine=str(d['cuisine'])[:80]
 p.taste_vector=taste_vector(p.flavors,p.budget);p.save()
@api_view(['GET','POST'])
@permission_classes([AllowAny])
def recipes(request):
 if request.method=='GET':return Response([recipe_data(r) for r in Recipe.objects.select_related('author').all().order_by('-created')])
 if not request.user.is_authenticated:return fail('Please sign in.',401)
 try:
  d=request.data
  if not d.get('title'):return fail('Recipe title is required.')
  from .ingredient_lookup import estimate_named_ingredients
  if not isinstance(d.get('ingredients'),list) or not d['ingredients']:return fail('Add ingredient names, quantities and units.')
  try:quote=estimate_named_ingredients(d['ingredients'])
  except (ValueError,TypeError) as exc:return fail(str(exc))
  r=Recipe.objects.create(author=request.user,cost=quote['estimated_cost'],cost_details=quote,**{k:d[k] for k in ['title','description','cuisine','ingredients','steps','allergens','dietary','minutes','image'] if k in d})
  return Response(recipe_data(r),status=201)
 except Exception as e:return fail(str(e))
@api_view(['GET','PATCH','DELETE'])
@permission_classes([AllowAny])
def recipe(request,pk):
 r=get_object_or_404(Recipe,pk=pk)
 if request.method=='GET':return Response(recipe_data(r))
 if not request.user.is_authenticated or not can_edit(request.user,r):return fail('Not allowed.',403)
 if request.method=='DELETE':r.delete();return Response({'ok':True})
 if 'ingredients' in request.data:
  from .ingredient_lookup import estimate_named_ingredients
  try:quote=estimate_named_ingredients(request.data['ingredients'])
  except (ValueError,TypeError) as exc:return fail(str(exc))
  r.cost=quote['estimated_cost'];r.cost_details=quote
 for k in ['title','description','cuisine','ingredients','steps','allergens','dietary','minutes','image']:
  if k in request.data:setattr(r,k,request.data[k])
 r.save();return Response(recipe_data(r))
@api_view(['GET','POST'])
@permission_classes([AllowAny])
def restaurants(request):
 if request.method=='GET':return Response([restaurant_data(r) for r in Restaurant.objects.prefetch_related('menu').all()])
 if not request.user.is_authenticated:return fail('Please sign in.',401)
 if not (request.user.is_staff or request.user.profile.role=='owner'):return fail('Restaurant owner role required.',403)
 d=request.data
 if not d.get('name') or not d.get('address'):return fail('Name and address are required.')
 r=Restaurant.objects.create(owner=request.user,**{k:d[k] for k in ['name','description','address','latitude','longitude','cuisine','image'] if k in d})
 return Response(restaurant_data(r),status=201)
@api_view(['GET','PATCH','DELETE'])
@permission_classes([AllowAny])
def restaurant(request,pk):
 r=get_object_or_404(Restaurant,pk=pk)
 if request.method=='GET':return Response(restaurant_data(r))
 if not request.user.is_authenticated or not can_edit(request.user,r):return fail('Not allowed.',403)
 if request.method=='DELETE':r.delete();return Response({'ok':True})
 for k in ['name','description','address','latitude','longitude','cuisine','image']:
  if k in request.data:setattr(r,k,request.data[k])
 r.save();return Response(restaurant_data(r))
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def menu_create(request,pk):
 r=get_object_or_404(Restaurant,pk=pk)
 if not can_edit(request.user,r):return fail('Not allowed.',403)
 d=request.data
 if not d.get('name') or d.get('price') is None:return fail('Name and price are required.')
 MenuItem.objects.create(restaurant=r,**{k:d[k] for k in ['name','description','price','allergens','dietary','image'] if k in d})
 return Response(restaurant_data(r),status=201)
@api_view(['PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def menu_detail(request,pk):
 m=get_object_or_404(MenuItem,pk=pk)
 if not can_edit(request.user,m.restaurant):return fail('Not allowed.',403)
 if request.method=='DELETE':m.delete();return Response({'ok':True})
 for k in ['name','description','price','allergens','dietary','image']:
  if k in request.data:setattr(m,k,request.data[k])
 m.save();return Response({'ok':True})
@api_view(['GET','POST'])
@permission_classes([AllowAny])
def reviews(request):
 if request.method=='GET':
  qs=Review.objects.all().order_by('-created')
  if request.query_params.get('recipe'):qs=qs.filter(recipe_id=request.query_params['recipe'])
  if request.query_params.get('restaurant'):qs=qs.filter(restaurant_id=request.query_params['restaurant'])
  return Response([review_data(r) for r in qs])
 if not request.user.is_authenticated:return fail('Please sign in.',401)
 d=request.data
 try:rating=int(d.get('rating',0))
 except:rating=0
 if rating not in range(1,6) or not d.get('comment'):return fail('A rating (1–5) and comment are required.')
 if bool(d.get('recipe'))==bool(d.get('restaurant')):return fail('Choose one recipe or restaurant.')
 if d.get('recipe'):get_object_or_404(Recipe,pk=d['recipe'])
 if d.get('restaurant'):get_object_or_404(Restaurant,pk=d['restaurant'])
 r=Review.objects.create(author=request.user,rating=rating,comment=d['comment'],recipe_id=d.get('recipe'),restaurant_id=d.get('restaurant'))
 return Response(review_data(r),status=201)
@api_view(['PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def review(request,pk):
 r=get_object_or_404(Review,pk=pk)
 if not can_edit(request.user,r):return fail('Not allowed.',403)
 if request.method=='DELETE':
  if request.user.is_staff:ModerationLog.objects.create(admin=request.user,action='delete_review',target=str(r.pk))
  r.delete();return Response({'ok':True})
 if 'rating' in request.data:
  try:v=int(request.data['rating'])
  except:return fail('Invalid rating.')
  if v not in range(1,6):return fail('Rating must be 1–5.')
  r.rating=v
 if 'comment' in request.data:r.comment=request.data['comment']
 r.save();return Response(review_data(r))
@api_view(['GET','POST','DELETE'])
@permission_classes([IsAuthenticated])
def recommendations(request):
 if request.method=='GET':return Response([{'id':r.id,'filters':r.filters,'results':r.results,'created':r.created.isoformat()} for r in request.user.history.all().order_by('-created')])
 if request.method=='DELETE':
  ids=request.data.get('ids',[])
  if ids:request.user.history.filter(id__in=ids).delete()
  else:request.user.history.all().delete()
  return Response({'ok':True})
 d=request.data
 try:
  budget=float(d.get('budget') or request.user.profile.budget)
  if budget<=0 or budget>200:return fail('Budget must be between 1 and 200.')
 except:return fail('Invalid budget.')
 results=rank_options(request.user.profile,d,Recipe.objects.all(),Restaurant.objects.prefetch_related('menu').all())
 entry=Recommendation.objects.create(user=request.user,filters=dict(d),results=results)
 return Response({'id':entry.id,'results':results})
@api_view(['GET'])
@permission_classes([AllowAny])
def geocode(request):
 q=request.query_params.get('q','').strip()
 if len(q)<3:return fail('Enter at least 3 characters.')
 try:
  res=requests.get('https://nominatim.openstreetmap.org/search',params={'q':q,'format':'json','limit':5,'countrycodes':'lt','viewbox':'23.72,55.05,24.12,54.78','bounded':1},headers={'User-Agent':'NyamNyamCoursework/1.0 (educational demo)'},timeout=6)
  res.raise_for_status();return Response([{'label':x['display_name'],'lat':float(x['lat']),'lon':float(x['lon'])} for x in res.json()])
 except requests.RequestException:return fail('Location service is temporarily unavailable.',503)
@api_view(['GET','DELETE'])
@permission_classes([IsAuthenticated])
def admin_users(request):
 if not request.user.is_staff:return fail('Administrator only.',403)
 if request.method=='GET':return Response([me(u) for u in User.objects.all()])
 u=get_object_or_404(User,pk=request.data.get('id'))
 if u==request.user:return fail('You cannot delete your own administrator account here.')
 ModerationLog.objects.create(admin=request.user,action='delete_user',target=u.username);u.delete();return Response({'ok':True})

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def pantry(request):
 if request.method=='GET':return Response([{'id':x.id,'name':x.name,'quantity':x.quantity,'unit':x.unit} for x in request.user.pantry.order_by('name')])
 d=request.data
 try:
  name=str(d.get('name','')).strip();quantity=float(d.get('quantity',0));unit=str(d.get('unit','piece')).strip()
  if not name or not unit or quantity<=0:return fail('Name, unit and positive quantity are required.')
  x,_=PantryItem.objects.update_or_create(user=request.user,name=name,unit=unit,defaults={'quantity':quantity})
  return Response({'id':x.id,'name':x.name,'quantity':x.quantity,'unit':x.unit},status=201)
 except (TypeError,ValueError):return fail('Invalid quantity.')

@api_view(['PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def pantry_detail(request,pk):
 x=get_object_or_404(PantryItem,user=request.user,pk=pk)
 if request.method=='DELETE':x.delete();return Response({'ok':True})
 try:
  quantity=float(request.data.get('quantity',x.quantity))
  if quantity<=0:return fail('Quantity must be positive.')
  x.quantity=quantity;x.save();return Response({'id':x.id,'name':x.name,'quantity':x.quantity,'unit':x.unit})
 except (TypeError,ValueError):return fail('Invalid quantity.')

@api_view(['GET','POST'])
@permission_classes([AllowAny])
def ingredient_prices(request):
 if request.method=='GET':return Response([{'name':x.name,'unit':x.unit,'price':float(x.price),'source':x.source,'updated':x.updated.isoformat()} for x in IngredientPrice.objects.all().order_by('name')])
 if not request.user.is_authenticated or not request.user.is_staff:return fail('Administrator only.',403)
 try:
  name=str(request.data.get('name','')).strip();price=float(request.data.get('price',-1));unit=str(request.data.get('unit','')).strip()
  if not name or not unit or price<0:return fail('Valid ingredient, unit and price are required.')
  obj,_=IngredientPrice.objects.update_or_create(name__iexact=name,defaults={'name':name,'unit':unit,'price':price,'source':str(request.data.get('source','Manual reference catalog'))})
  return Response({'id':obj.id,'name':obj.name},status=201)
 except (ValueError,TypeError):return fail('Invalid ingredient price.')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recipe_estimate(request):
 items=request.data.get('ingredients',[])
 if not isinstance(items,list):return fail('Ingredients must be a list.')
 catalog={x.name.casefold():{'unit':x.unit,'price':x.price} for x in IngredientPrice.objects.all()}
 try:return Response(estimate_cost(items,catalog))
 except (ValueError,TypeError) as e:return fail(str(e))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recipe_estimate_live(request):
 from .live_prices import live_recipe_cost
 try:
  return Response(live_recipe_cost(request.data.get('ingredients', []),
      currency=request.data.get('currency', 'EUR'), country=request.data.get('country', 'LT')))
 except (ValueError, TypeError) as exc:
  return fail(str(exc))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recipe_estimate_named(request):
 from .ingredient_lookup import estimate_named_ingredients
 try:return Response(estimate_named_ingredients(request.data.get('ingredients',[])))
 except (ValueError,TypeError) as exc:return fail(str(exc))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
 from django.core.files.storage import default_storage
 from django.core.files.base import ContentFile
 from uuid import uuid4
 f=request.FILES.get('file')
 if not f:return fail('Select an image file.')
 if f.size>5*1024*1024:return fail('Image must be smaller than 5 MB.')
 from PIL import Image, UnidentifiedImageError
 try:
  f.seek(0);im=Image.open(f);im.verify();f.seek(0)
  if im.format not in ('JPEG','PNG','WEBP'):return fail('Use JPEG, PNG or WebP images.')
  ext={'JPEG':'jpg','PNG':'png','WEBP':'webp'}[im.format]
 except (UnidentifiedImageError,OSError):return fail('Invalid image.')
 path=default_storage.save(f'uploads/{uuid4().hex}.{ext}',ContentFile(f.read()))
 return Response({'url':request.build_absolute_uri('/media/'+path)})


@api_view(['GET'])
@permission_classes([AllowAny])
def nearby_restaurants(request):
    """Find restaurants using saved coordinates; never depends on Overpass uptime."""
    from .distance import distance_km
    try:
        lat = float(request.query_params['lat'])
        lon = float(request.query_params['lon'])
        radius = float(request.query_params.get('radius', 10))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 < radius <= 200):
            raise ValueError()
    except (ValueError, TypeError, KeyError):
        return fail('Invalid location or radius (0–200 km).')
    matches = []
    for restaurant in Restaurant.objects.filter(latitude__isnull=False, longitude__isnull=False).prefetch_related('menu'):
        distance = distance_km(lat, lon, restaurant.latitude, restaurant.longitude)
        if distance <= radius:
            row = restaurant_data(restaurant)
            row['distance_km'] = distance
            matches.append(row)
    matches.sort(key=lambda r: (r['distance_km'], r['name']))
    return Response(matches)
