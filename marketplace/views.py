from datetime import date, datetime
from django.shortcuts import render, get_object_or_404, redirect
from .context_processors import get_cart_amount, get_cart_counter
from vendor.models import Vendor, OpeningHour
from django.http import JsonResponse,  HttpResponse

from menu.models import Category, FoodItem
from django.db.models import Prefetch, Q
from .models import Cart

from django.contrib.auth.decorators import login_required

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

# Create your views here.

def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active = True).order_by('created_at')
    vendor_count = vendors.count()
    context = {
        'vendors': vendors,
        'vendor_count':vendor_count,
    }
    return render(request, 'marketplace/listings.html', context)

def vendor_detail(request, vendor_slug = None):
    vendor = get_object_or_404(Vendor, vendor_slug = vendor_slug)

    categories = Category.objects.filter(vendor = vendor).prefetch_related(
        Prefetch(
            'fooditems',
            queryset = FoodItem.objects.filter(is_available = True),
        )
    )

    opening_hours = OpeningHour.objects.filter(vendor = vendor).order_by('day', '-from_hour')

    today_date = date.today()
    today = today_date.isoweekday()
    current_opening_hours = OpeningHour.objects.filter(vendor=vendor, day = today)
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user = request.user)
    else:
        cart_items = None
    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
        'opening_hours': opening_hours,
        'current_opening_hours': current_opening_hours,
    }
    return render(request, 'marketplace/vendor_detail.html', context)

def add_to_cart(request, food_id = None):
    if request.user.is_authenticated:
        if request.is_ajax():
            try:
                food_item = FoodItem.objects.get(id = food_id)
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem = food_item)
                    chkCart.quantity = chkCart.quantity + 1
                    chkCart.save()
                    return JsonResponse({'status':'Success', 'message':'Increased the cart quantity', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity, 'cart_amount': get_cart_amount(request)})
                except:
                    chkCart = Cart.objects.create(user = request.user, fooditem = food_item, quantity = 1)
                    return JsonResponse({'status':'Success', 'message':'Added the food to the cart', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity, 'cart_amount': get_cart_amount(request)})
            except:
                return JsonResponse({'status':'Failed', 'message':'This food does not exist'})
        else:
            return JsonResponse({'status':'Failed', 'message':'Invalid request'})

    else:
        return JsonResponse({'status':'login_required', 'message':'Please login to continue'})

def decrease_cart(request, food_id = None):
    if request.user.is_authenticated:
        if request.is_ajax():
        # if request.headers.get('x-requested-with') == 'XMLHttpRequest':   # in Django 4.0 to check whether it is ajax request or not
            try:
                food_item = FoodItem.objects.get(id = food_id)
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem = food_item)
                    if chkCart.quantity > 1:
                        chkCart.quantity = chkCart.quantity - 1
                        chkCart.save()
                    else:
                        chkCart.delete()
                        chkCart.quantity = 0
                        # return JsonResponse({'status':'Success!!', 'message':'Cart item has been removed!', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity})
                    return JsonResponse({'status':'Success', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity, 'cart_amount': get_cart_amount(request)})
                except:
                    return JsonResponse({'status':'Failed', 'message':'You do not have this item in your cart!'})
            except:
                return JsonResponse({'status':'Failed', 'message':'This food does not exist'})
        else:
            return JsonResponse({'status':'Failed', 'message':'Invalid request'})

    else:
        return JsonResponse({'status':'login_required', 'message':'Please login to continue'})

@login_required(login_url = 'login')
def cart(request):
    cart_items = Cart.objects.filter(user = request.user).order_by("created_at")
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/cart.html', context)

def delete_cart(request, cart_id):
    if request.user.is_authenticated:
        if request.is_ajax():
            try:
                cart_item = Cart.objects.get(user = request.user, id = cart_id)
                # print("********")
                # print(cart_item)
                if cart_item:
                    cart_item.delete()
                    return JsonResponse({'status':'Success', 'message':'Cart item has been deleted!', 'cart_counter': get_cart_counter(request), 'cart_amount': get_cart_amount(request) })
            except:
                return JsonResponse({'status':'Failed', 'message':'Cart Item does not exist!'})
        else:
            return JsonResponse({'status':'Failed', 'message':'Invalid request'})

def search(request):
    if not 'address' in request.GET:
        return redirect('marketplace')
    else:
        address = request.GET["address"]
        latitude = request.GET['lat']
        longitude = request.GET['lng']
        radius = request.GET['radius']
        keyword = request.GET['keyword']
        fetch_vendors_by_fooditems = FoodItem.objects.filter(food_title__icontains = keyword, is_available = True).values_list('vendor', flat=True)
        vendors = Vendor.objects.filter(Q(id__in = fetch_vendors_by_fooditems) | Q(vendor_name__icontains = keyword, is_approved = True, user__is_active = True))
        if latitude and longitude and radius:
            pnt = GEOSGeometry('Point(%s %s)' % (longitude, latitude))
            vendors = Vendor.objects.filter(Q(id__in = fetch_vendors_by_fooditems) | Q(vendor_name__icontains = keyword, is_approved = True, user__is_active = True), 
                                                user_profile__location__distance_lte = (pnt, D(km=radius))
                                                ).annotate(distance=Distance("user_profile__location", pnt)).order_by("distance")
            for v in vendors:
                v.kms = round(v.distance.km, 1)
        vendor_count = vendors.count()
        context = {
            'vendors':vendors,
            'vendor_count':vendor_count,
            'source_location': address,
        }
        return render(request, 'marketplace/listings.html', context)