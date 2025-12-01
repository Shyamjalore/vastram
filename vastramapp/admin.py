# admin.py - Fixed
from django.contrib import admin
from django.utils.html import format_html
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'actual_price', 'special_price', 'stock', 'sales_count', 'is_active', 'is_featured']
    list_filter = ['category', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_percentage', 'target_audience', 'is_active', 'created_at']
    list_filter = ['target_audience', 'is_active', 'created_at']
    search_fields = ['title', 'description']

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'city', 'state', 'pincode', 'created_at']
    list_filter = ['city', 'state', 'created_at']
    search_fields = ['full_name', 'user__username', 'city']
    readonly_fields = ['created_at']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'price', 'get_total_price']
    can_delete = False
    extra = 0
    
    def get_total_price(self, obj):
        return obj.total_price()
    get_total_price.short_description = 'Total Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'total_amount', 'status', 'created_at', 'shipping_address_display']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'order_id', 'shipping_address__full_name']
    readonly_fields = ['created_at', 'updated_at', 'order_id']
    inlines = [OrderItemInline]
    
    def shipping_address_display(self, obj):
        if obj.shipping_address:
            return f"{obj.shipping_address.full_name}, {obj.shipping_address.city}"
        return "No shipping address"
    shipping_address_display.short_description = 'Shipping Address'

@admin.register(OrderFeedback)
class OrderFeedbackAdmin(admin.ModelAdmin):
    list_display = ['order', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    readonly_fields = ['created_at']

@admin.register(UserLoginHistory)
class UserLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'ip_address', 'device_id']
    list_filter = ['login_time']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['login_time']

@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']

@admin.register(ContactQuery)
class ContactQueryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', resolved_at=timezone.now())
    mark_resolved.short_description = "Mark selected queries as resolved"
    
    actions = [mark_resolved]

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_date', 'is_active', 'created_at']
    list_filter = ['is_active', 'event_date', 'created_at']
    search_fields = ['title', 'description']

# Custom User Admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class UserLoginHistoryInline(admin.TabularInline):
    model = UserLoginHistory
    extra = 0
    readonly_fields = ['login_time', 'ip_address', 'user_agent', 'device_id']
    can_delete = False
    max_num = 5  # Show only last 5 logins

class UserAdmin(BaseUserAdmin):
    inlines = [UserLoginHistoryInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login_display', 'login_count']
    
    def last_login_display(self, obj):
        last_login = UserLoginHistory.objects.filter(user=obj).order_by('-login_time').first()
        return last_login.login_time if last_login else 'Never'
    last_login_display.short_description = 'Last Login'
    
    def login_count(self, obj):
        return UserLoginHistory.objects.filter(user=obj).count()
    login_count.short_description = 'Login Count'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Cart)
admin.site.register(Wishlist)