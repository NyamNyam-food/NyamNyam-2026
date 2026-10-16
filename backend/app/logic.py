"""Transparent matching, graph ranking, allergy filtering and price estimation."""
import math
from collections import defaultdict
from django.db.models import Avg

FLAVORS=['sweet','savory','spicy','sour','bitter']

def taste_vector(flavors,budget):
    values=[max(0,min(5,float(flavors.get(k,3))))/5 for k in FLAVORS]+[max(0,min(float(budget),200))/200]
    norm=math.sqrt(sum(v*v for v in values)) or 1
    return [round(v/norm,6) for v in values]

def cosine(a,b):
    if not a or not b or len(a)!=len(b):return 0.0
    denom=math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
    return sum(x*y for x,y in zip(a,b))/denom if denom else 0.0

def haversine(lat1,lon1,lat2,lon2):
    lat1,lon1,lat2,lon2=map(math.radians,map(float,[lat1,lon1,lat2,lon2]))
    dlat=lat2-lat1;dlon=lon2-lon1
    a=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371*2*math.asin(min(1,math.sqrt(a)))

def pagerank(graph,damping=.85,iterations=100,tolerance=1e-10):
    """Actual power-iteration PageRank on a directed weighted graph."""
    nodes=list(graph)
    if not nodes:return {}
    n=len(nodes);scores={node:1/n for node in nodes}
    for _ in range(iterations):
        incoming={node:(1-damping)/n for node in nodes}
        for source,edges in graph.items():
            total=sum(max(0,w) for w in edges.values())
            if total:
                for target,weight in edges.items():
                    if target in incoming:incoming[target]+=damping*scores[source]*max(0,weight)/total
            else:
                for target in nodes:incoming[target]+=damping*scores[source]/n
        delta=sum(abs(incoming[x]-scores[x]) for x in nodes)
        scores=incoming
        if delta<tolerance:break
    return scores

def estimate_cost(ingredients,price_catalog):
    """Calculate recipe cost from structured quantities and unit-specific prices.
    Unknown ingredients are reported, never silently assigned fake prices.
    """
    total=0.0;missing=[]
    for item in ingredients:
        if not isinstance(item,dict) or not all(k in item for k in ('name','quantity','unit')):
            missing.append(str(item));continue
        key=item['name'].strip().casefold();record=price_catalog.get(key)
        if not record or record['unit'].casefold()!=str(item['unit']).casefold():
            missing.append(item['name']);continue
        amount=float(item['quantity'])
        if amount<0:raise ValueError('Ingredient quantities must be non-negative')
        total+=amount*float(record['price'])
    return {'estimated_cost':round(total,2),'missing_prices':missing,'complete':not missing}

def _rating(obj):
    return obj.reviews.aggregate(v=Avg('rating'))['v'] or 3.5

def rank_options(profile,filters,recipes,restaurants):
    """Hard safety constraints, k-nearest taste matching and graph PageRank.
    Graph nodes are candidates. Weighted edges connect options sharing cuisine,
    dietary attributes and flavor. Personalized taste similarity contributes
    to final scores alongside genuine iterative graph centrality.
    """
    budget=float(filters.get('budget') or profile.budget or 25)
    if not 0<budget<=200:raise ValueError('Budget must be between 1 and 200')
    mode=filters.get('mode','all');cuisine=(filters.get('cuisine') or profile.cuisine or '').casefold()
    mood=str(filters.get('mood','')).casefold()
    exclusions={str(x).casefold() for x in profile.allergies}
    dietary={str(x).casefold() for x in profile.dietary}
    location=filters.get('location') or {}
    radius=filters.get('radius_km')
    radius=float(radius) if radius not in (None,'') else None
    if radius is not None and radius<=0:raise ValueError('Distance must be positive')
    candidates=[]
    def safe(labels,allergens,price):
        return not (exclusions & {str(x).casefold() for x in allergens}) and dietary.issubset({str(x).casefold() for x in labels}) and float(price)<=budget
    if mode in ('all','home'):
        for r in recipes:
            if getattr(r,'cost_details',None) and not r.cost_details.get('complete',False):continue
            if not safe(r.dietary,r.allergens,r.cost):continue
            candidates.append(dict(type='recipe',id=r.id,title=r.title,subtitle=r.cuisine,price=float(r.cost),image=r.image,rating=round(_rating(r),1),dietary=r.dietary,description=r.description,flavors=getattr(r,'flavors',{}),distance_km=None))
    if mode in ('all','restaurant'):
        for r in restaurants:
            matching=[m for m in r.menu.all() if safe(m.dietary,m.allergens,m.price)]
            if not matching:continue
            distance=None
            if location and 'lat' in location and 'lon' in location:
                if r.latitude is None or r.longitude is None:continue
                distance=haversine(location['lat'],location['lon'],r.latitude,r.longitude)
                if radius is not None and distance>radius:continue
            elif radius is not None:continue
            candidates.append(dict(type='restaurant',id=r.id,title=r.name,subtitle=r.cuisine,price=min(float(m.price) for m in matching),image=r.image,rating=round(_rating(r),1),dietary=matching[0].dietary,description=r.description,flavors={},distance_km=round(distance,2) if distance is not None else None))
    if not candidates:return []
    # k-nearest neighbours in normalized flavor-budget feature space.
    target=profile.taste_vector or taste_vector(profile.flavors,profile.budget)
    for c in candidates:
        flavor=c['flavors'] if c['flavors'] else {k:(4 if mood and mood in c['description'].casefold() else 3) for k in FLAVORS}
        vec=taste_vector(flavor,c['price'])
        c['taste_similarity']=max(0,cosine(target,vec))
    neighbors=sorted(candidates,key=lambda c:c['taste_similarity'],reverse=True)[:min(7,len(candidates))]
    neighbor_keys={(c['type'],c['id']) for c in neighbors}
    graph={i:{} for i in range(len(candidates))}
    for i,a in enumerate(candidates):
        for j,b in enumerate(candidates):
            if i==j:continue
            weight=.05
            if a['subtitle'].casefold()==b['subtitle'].casefold():weight+=1.0
            weight+=.25*len({x.casefold() for x in a['dietary']} & {x.casefold() for x in b['dietary']})
            weight+=.4*max(0,1-abs(a['price']-b['price'])/max(budget,1))
            if (b['type'],b['id']) in neighbor_keys:weight+=.7
            graph[i][j]=weight
    pr=pagerank(graph);highest=max(pr.values()) or 1
    for i,c in enumerate(candidates):
        rating=c['rating']/5
        price_score=1-c['price']/budget
        cuisine_match=1 if cuisine and cuisine in c['subtitle'].casefold() else (.5 if not cuisine else 0)
        proximity=1/(1+c['distance_km']/10) if c['distance_km'] is not None else .5
        c['score']=round(.28*c['taste_similarity']+.22*pr[i]/highest+.20*rating+.12*price_score+.10*cuisine_match+.08*proximity,5)
        c['reason']='Allergy-safe match · taste similarity {:.0%} · graph-ranked'.format(c['taste_similarity'])
        del c['dietary'];del c['description'];del c['flavors'];del c['taste_similarity']
    return sorted(candidates,key=lambda c:c['score'],reverse=True)[:24]
