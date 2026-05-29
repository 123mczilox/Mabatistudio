from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from core.supa_storage import upload_image


# =========================
# PRODUCT TYPE
# =========================
class ProductType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = 'Product Type'
        verbose_name_plural = 'Product Types'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# =========================
# COLOR VARIANT
# =========================
class ColorVariant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    hex_code = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        verbose_name = 'Color Variant'
        verbose_name_plural = 'Color Variants'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# =========================
# PRODUCT
# =========================
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
    price = models.DecimalField(max_digits=10, decimal_places=2)

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
        # -------------------------
        # SLUG GENERATION
        # -------------------------
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1

            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug

        # -------------------------
        # SAVE FIRST
        # -------------------------
        super().save(*args, **kwargs)

        # -------------------------
        # UPLOAD TO SUPABASE S3
        # -------------------------
        if self.image and not self.image_url:
            try:
                self.image.file.seek(0)

                url = upload_image(self.image.file, self.image.name)

                Product.objects.filter(pk=self.pk).update(
                    image_url=url
                )

            except Exception as e:
                print("IMAGE UPLOAD ERROR:", e)

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    @property
    def main_image_url(self):
        if self.image_url:
            return self.image_url

        first = self.images.first()
        if first and first.image:
            return first.image.url

        return ''


# =========================
# PRODUCT IMAGES
# =========================
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

    def __str__(self):
        return f"{self.product.name} - {self.view_type}"


# =========================
# CONTACT MESSAGE
# =========================
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


# =========================
# GALLERY IMAGE
# =========================
class GalleryImage(models.Model):
    image = models.ImageField(upload_to='gallery/')
    title = models.CharField(max_length=200, blank=True)
    caption = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return self.title or f"Gallery {self.id}"