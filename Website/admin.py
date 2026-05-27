from django.contrib import admin
from django.utils.html import format_html
from .models import ContactMessage, Product, ProductImage, RoofType, ColorVariant, GalleryImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;" />', obj.image.url)
        return ''
    preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'roof_type', 'price', 'gauge', 'featured', 'created_at', 'thumbnail')
    search_fields = ('name', 'description')
    list_filter = ('roof_type', 'featured', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ('thumbnail',)

    def thumbnail(self, obj):
        url = obj.main_image_url
        if url:
            return format_html('<img src="{}" style="height:60px;" />', url)
        return '-'
    thumbnail.short_description = 'Image'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'view_type', 'order', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;" />', obj.image.url)
        return ''
    preview.short_description = 'Preview'


@admin.register(RoofType)
class RoofTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'hex_code')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'submitted_at', 'is_read')
    list_filter = ('is_read', 'submitted_at')
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('name', 'email', 'phone', 'message', 'submitted_at')
    ordering = ('-submitted_at',)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'order', 'preview')
    readonly_fields = ('preview',)
    list_display_links = ('title',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;" />', obj.image.url)
        return ''
    preview.short_description = 'Preview'
