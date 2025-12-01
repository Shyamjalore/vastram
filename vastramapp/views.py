from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import uuid
from .models import *
from .forms import SignUpForm

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def track_user_login(request, user):
    # Generate a simple device ID based on user agent and IP
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    device_id = f"{ip_address}-{hash(user_agent) % 10000}"
    
    UserLoginHistory.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        device_id=device_id
    )

def home(request):
    categories = Category.objects.all()
    
    # Dynamic Sliders
    sliders = Slider.objects.filter(is_active=True).order_by('-created_at')[:4]
    
    # Featured Products - Most sold products
    featured_products = Product.objects.filter(is_active=True).order_by('-sales_count')[:8]
    
    # New Arrivals - Last 30 days products
    from django.utils import timezone
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_arrivals = Product.objects.filter(
        is_active=True, 
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')[:8]
    
    # Most Discounted Products - Fixed query
    most_discounted = Product.objects.filter(
        is_active=True,
        actual_price__gt=F('special_price')
    ).annotate(
        discount_diff=F('actual_price') - F('special_price')
    ).order_by('-discount_diff')[:8]
    
    # Special Offers
    special_offers = SpecialOffer.objects.filter(is_active=True).order_by('-created_at')[:1]
    
    return render(request, 'home.html', {
        'categories': categories,
        'sliders': sliders,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'most_discounted': most_discounted,
        'special_offers': special_offers,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Get 6 latest products from the same category
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id).order_by('-created_at')[:6]
    
    return render(request, 'product_detail.html', {
        'product': product,
        'related_products': related_products
    })

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category, is_active=True)
    return render(request, 'category_products.html', {
        'products': products,
        'categories': Category.objects.all(),
        'selected_category': category
    })

def search_products(request):
    query = request.GET.get('q')
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    return render(request, 'search_result.html', {
        'products': products,
        'categories': Category.objects.all(),
        'search_query': query
    })

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to add items to cart!')
        return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f'{product.name} added to cart!')
    return redirect('cart')

def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        # For logged in users
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        if created:
            messages.success(request, f'{product.name} added to wishlist!')
            return JsonResponse({'status': 'success', 'message': 'Added to wishlist!'})
        else:
            messages.info(request, f'{product.name} is already in your wishlist!')
            return JsonResponse({'status': 'info', 'message': 'Already in wishlist!'})
    else:
        # For non-logged in users - using session
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
            
        wishlist_item, created = Wishlist.objects.get_or_create(
            session_key=session_key,
            product=product
        )
        if created:
            messages.success(request, f'{product.name} added to wishlist!')
            return JsonResponse({'status': 'success', 'message': 'Added to wishlist!'})
        else:
            messages.info(request, f'{product.name} is already in your wishlist!')
            return JsonResponse({'status': 'info', 'message': 'Already in wishlist!'})

@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('cart')

@login_required
def update_cart_quantity(request, cart_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })

def remove_from_wishlist(request, wishlist_id):
    if request.user.is_authenticated:
        wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    else:
        session_key = request.session.session_key
        wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, session_key=session_key)
    
    wishlist_item.delete()
    messages.success(request, 'Item removed from wishlist!')
    return redirect('wishlist')

def wishlist_view(request):
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    else:
        session_key = request.session.session_key
        wishlist_items = Wishlist.objects.filter(session_key=session_key).select_related('product')
    
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def checkout_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart')
    
    total_amount = sum(item.total_price() for item in cart_items)
    
    if request.method == 'POST':
        # Shipping address data collect karo
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        
        # Validate required fields
        if not all([full_name, phone, address, city, state, pincode]):
            messages.error(request, 'Please fill all the shipping information fields!')
            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total_amount': total_amount
            })
        
        try:
            # Shipping address create karo
            shipping_address = ShippingAddress.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                address=address,
                city=city,
                state=state,
                pincode=pincode
            )
            
            # Order create karo with unique ID
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                total_amount=total_amount
            )
            
            # Order items create karo with proper price
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.special_price  # Ensure price is set
                )
                # Update sales count
                cart_item.product.sales_count += cart_item.quantity
                cart_item.product.save()
            
            # Cart clear karo
            cart_items.delete()
            
            messages.success(request, f'Order #{order.order_id} placed successfully!')
            return redirect('order_history')
            
        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total_amount': total_amount
            })
    
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})

@login_required
@require_POST
def submit_feedback(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    rating = request.POST.get('rating')
    comment = request.POST.get('comment')
    
    if not rating or not comment:
        messages.error(request, 'Please provide both rating and comment.')
        return redirect('order_history')
    
    OrderFeedback.objects.create(
        order=order,
        rating=int(rating),
        comment=comment
    )
    
    messages.success(request, 'Thank you for your feedback!')
    return redirect('order_history')

def about_us(request):
    about_content = AboutUs.objects.filter(is_active=True).first()
    return render(request, 'about_us.html', {'about_content': about_content})

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if not all([name, email, subject, message]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'contact_us.html')
        
        ContactQuery.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        
        messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
        return redirect('contact_us')
    
    return render(request, 'contact_us.html')

def events(request):
    events_list = Event.objects.filter(is_active=True).order_by('-event_date')
    return render(request, 'events.html', {'events': events_list})

@login_required
def profile(request):
    user = request.user
    orders_count = Order.objects.filter(user=user).count()
    wishlist_count = Wishlist.objects.filter(user=user).count()
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'profile.html', {
        'orders_count': orders_count,
        'wishlist_count': wishlist_count
    })
    
