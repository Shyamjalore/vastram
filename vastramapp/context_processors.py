# context_processors.py - Updated
from .models import Category, Cart, Wishlist

def categories(request):
    return {
        'categories': Category.objects.all()
    }
    
def cart_count(request):
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()
    else:
        cart_count = 0
    return {'cart_count': cart_count}

def wishlist_count(request):
    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    else:
        session_key = request.session.session_key
        if session_key:
            wishlist_count = Wishlist.objects.filter(session_key=session_key).count()
        else:
            wishlist_count = 0
    return {'wishlist_count': wishlist_count}