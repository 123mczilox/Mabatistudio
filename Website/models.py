import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from core.supa_storage import upload_image, get_public_url


class ProductType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = 'Product Type'
        verbose_name_plural = 'Product Types'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ColorVariant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    hex_code = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        verbose_name = 'Color Variant'
        verbose_name_plural = 'Color Variants'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )

    gauge = models.CharField(max_length=20, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    color_variants = models.ManyToManyField(
        ColorVariant,
        blank=True,
        related_name='products'
    )

    warranty = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    features = models.JSONField(blank=True, null=True, default=list)

    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-featured', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # STEP 1: slug generation
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1

            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug

        # STEP 2: save first (important)
        super().save(*args, **kwargs)

        # STEP 3: upload to Supabase safely only when not using Django S3 storage
        if self.image and not self.image_url and not settings.DJANGO_USE_S3:
            try:
                with self.image.open("rb") as f:
                    url = upload_image(f, self.image.name)

                if url:
                    self.image_url = url
                    Product.objects.filter(pk=self.pk).update(image_url=url)

            except Exception as e:
                print("Image upload failed:", e)

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    @property
    def display_price(self):
        if self.price is not None:
            return self.price
        first_variant = self.gauge_variants.order_by('order').select_related('gauge').first()
        return first_variant.price if first_variant else Decimal('0')

    @property
    def display_gauges(self):
        if self.gauge:
            return self.gauge
        variants = self.gauge_variants.select_related('gauge').all()
        labels = [variant.gauge.name for variant in variants if variant.gauge]
        if not labels:
            return '-'
        unique_labels = sorted(dict.fromkeys(labels))
        return ', '.join(unique_labels)

    @property
    def has_gauge_variants(self):
        return self.gauge_variants.exists()

    @property
    def main_image_url(self):
        if self.image_url:
            return self.image_url

        if self.image:
            try:
                return self.image.url
            except Exception:
                return get_public_url(str(self.image))

        first = self.images.first() if hasattr(self, 'images') else None
        if first and first.image:
            try:
                return first.image.url
            except Exception:
                return get_public_url(str(first.image))

        return ''


class ProductImage(models.Model):
    VIEW_CHOICES = [
        ('front', 'Front'),
        ('side', 'Side'),
        ('top', 'Top'),
        ('detail', 'Detail'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(upload_to='products/gallery/')
    view_type = models.CharField(max_length=20, choices=VIEW_CHOICES, default='front')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    @property
    def image_url(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                return get_public_url(str(self.image))
        return ''

    def __str__(self):
        return f"{self.product.name} - {self.view_type}"


class RoofingProfile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    cover_width = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    default_sheet_price = models.DecimalField(max_digits=10, decimal_places=2, default=1800)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Roofing Profile'
        verbose_name_plural = 'Roofing Profiles'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class RoofGauge(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=3, default=1.0)
    additional_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Roof Gauge'
        verbose_name_plural = 'Roof Gauges'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductGaugeVariant(models.Model):
    """Links Product to Gauge with custom pricing per gauge variant"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='gauge_variants'
    )
    gauge = models.ForeignKey(RoofGauge, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    finish_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., Matt Finish, Glossy, etc."
    )
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'gauge', 'finish_type')
        ordering = ['order', 'gauge__order']
        verbose_name = 'Product Gauge Variant'
        verbose_name_plural = 'Product Gauge Variants'

    def __str__(self):
        return f"{self.product.name} - {self.gauge.name} ({self.finish_type or 'Standard'}) - KES {self.price}"


class RoofEstimate(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('quote_ready', 'Quote Ready'),
        ('approved', 'Approved'),
        ('expired', 'Expired'),
    ]
    
    CALCULATION_METHODS = [
        ('dimensions', 'Dimensions (Length × Width)'),
        ('direct_area', 'Direct Area (m²)'),
    ]

    quote_number = models.CharField(max_length=40, unique=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    customer_full_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_email = models.EmailField(blank=True)
    project_location = models.CharField(max_length=250, blank=True)
    project_county = models.CharField(max_length=100, blank=True)
    customer_notes = models.TextField(blank=True)
    calculation_method = models.CharField(max_length=20, choices=CALCULATION_METHODS, default='dimensions')
    roof_type = models.CharField(max_length=100)
    profile = models.ForeignKey(RoofingProfile, on_delete=models.SET_NULL, null=True)
    gauge = models.ForeignKey(RoofGauge, on_delete=models.SET_NULL, null=True)
    color = models.CharField(max_length=100, blank=True)
    length = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    width = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    direct_area = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Used when calculation_method is 'direct_area'")
    pitch = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    include_screws = models.BooleanField(default=True)
    include_nails = models.BooleanField(default=True)
    include_timber = models.BooleanField(default=True)
    include_rainwater = models.BooleanField(default=True)
    rainfall = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    roof_area = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recommended_sheets = models.PositiveIntegerField(default=0)
    ridge_caps = models.PositiveIntegerField(default=0)
    screws = models.PositiveIntegerField(default=0)
    nails = models.PositiveIntegerField(default=0)
    timber_length = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rainwater_litres = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    eaves = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sheet_total_width = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sheet_total_length = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    side_lap = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    end_lap = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    end_overhang = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sheet_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ridge_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    screw_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nail_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    timber_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labour_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    material_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Roof Estimate'
        verbose_name_plural = 'Roof Estimates'
        ordering = ['-created_at']

    def __str__(self):
        return self.quote_number or f"Estimate {self.pk}"

    def save(self, *args, **kwargs):
        if not self.quote_number:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.quote_number = f'RH-{timestamp}-{uuid.uuid4().hex[:4].upper()}'
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.name} <{self.email}>"


class GalleryImage(models.Model):
    image = models.ImageField(upload_to='gallery/')
    title = models.CharField(max_length=200, blank=True)
    caption = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', '-uploaded_at']

    @property
    def image_url(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                return get_public_url(str(self.image))
        return ''

    def __str__(self):
        return self.title or str(self.image.name)