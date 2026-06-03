from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q

# Customize the Django admin site appearance
admin.site.site_header = "MabatiHubKenya Admin"
admin.site.site_title = "MabatiHubKenya Admin Portal"
admin.site.index_title = "MabatiHubKenya Administration"
from .models import (
    Product,
    ColorVariant,
    ProductType,
    ContactMessage,
    GalleryImage,
    ProductImage,
    RoofingProfile,
    RoofGauge,
    RoofEstimate,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('preview',)
    fields = ('image', 'view_type', 'alt_text', 'order', 'preview')
    ordering = ('order',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;" />', obj.image.url)
        return ''
    preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_type', 'price', 'gauge', 'featured', 'created_at', 'thumbnail')
    list_display_links = ('name',)
    list_editable = ('price', 'gauge', 'featured')
    list_per_page = 25
    search_fields = ('name', 'description')
    list_filter = ('product_type', 'featured', 'created_at', 'color_variants')
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ('thumbnail',)
    filter_horizontal = ('color_variants',)
    autocomplete_fields = ('product_type',)

    def thumbnail(self, obj):
        url = obj.main_image_url
        if url:
            return format_html('<img src="{}" style="height:60px;" />', url)
        return '-'
    thumbnail.short_description = 'Image'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'view_type', 'order', 'preview')
    list_editable = ('order',)
    list_filter = ('view_type',)
    search_fields = ('product__name',)
    list_per_page = 50
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;" />', obj.image.url)
        return ''
    preview.short_description = 'Preview'


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'hex_code')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('hex_code',)
    search_fields = ('name', 'hex_code')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'submitted_at', 'is_read')
    list_filter = ('is_read', 'submitted_at')
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('name', 'email', 'phone', 'message', 'submitted_at')
    ordering = ('-submitted_at',)
    actions = ('mark_as_read', 'mark_as_unread')

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} message(s) marked as read.")
    mark_as_read.short_description = 'Mark selected messages as read'

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} message(s) marked as unread.")
    mark_as_unread.short_description = 'Mark selected messages as unread'


@admin.register(RoofingProfile)
class RoofingProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'cover_width', 'default_sheet_price', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_editable = ('cover_width', 'default_sheet_price', 'order')


@admin.register(RoofGauge)
class RoofGaugeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_multiplier', 'additional_cost', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_editable = ('price_multiplier', 'additional_cost', 'order')


@admin.register(RoofEstimate)
class RoofEstimateAdmin(admin.ModelAdmin):
    list_display = ('quote_number', 'roof_type', 'profile', 'gauge', 'grand_total', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'profile', 'gauge')
    search_fields = ('quote_number', 'roof_type', 'color')
    readonly_fields = ('quote_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'order', 'preview')
    list_editable = ('order',)
    list_filter = ('uploaded_at',)
    readonly_fields = ('preview',)
    list_display_links = ('title',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;" />', obj.image.url)
        return ''
    preview.short_description = 'Preview'


