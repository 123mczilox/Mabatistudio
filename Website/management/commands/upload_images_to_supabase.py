from django.core.management.base import BaseCommand
from django.conf import settings
from Website.models import Product, ProductImage, GalleryImage
from core.supa_storage import upload_image
import os


class Command(BaseCommand):
    help = 'Upload all existing product images to Supabase'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting image upload to Supabase...'))
        
        # Upload Product images
        self.stdout.write('\n--- Product Main Images ---')
        products = Product.objects.filter(image__isnull=False).exclude(image='')
        for product in products:
            if product.image:
                image_path = os.path.join(settings.MEDIA_ROOT, product.image.name)
                if os.path.exists(image_path):
                    try:
                        with open(image_path, 'rb') as f:
                            url = upload_image(f, product.image.name)
                        if url:
                            product.image_url = url
                            product.save(update_fields=['image_url'])
                            self.stdout.write(self.style.SUCCESS(f'✓ {product.name}: {product.image.name}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'✗ {product.name}: Upload returned None'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'✗ {product.name}: {e}'))
                else:
                    self.stdout.write(self.style.WARNING(f'- {product.name}: File not found ({image_path})'))

        # Upload ProductImage (gallery) images
        self.stdout.write('\n--- ProductImage Gallery Images ---')
        gallery_images = ProductImage.objects.filter(image__isnull=False).exclude(image='')
        for img in gallery_images:
            if img.image:
                image_path = os.path.join(settings.MEDIA_ROOT, img.image.name)
                if os.path.exists(image_path):
                    try:
                        with open(image_path, 'rb') as f:
                            url = upload_image(f, img.image.name)
                        if url:
                            self.stdout.write(self.style.SUCCESS(f'✓ {img.product.name} - {img.get_view_type_display()}: {img.image.name}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'✗ {img.product.name}: Upload returned None'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'✗ {img.product.name}: {e}'))
                else:
                    self.stdout.write(self.style.WARNING(f'- {img.product.name}: File not found ({image_path})'))

        # Upload GalleryImage images
        self.stdout.write('\n--- GalleryImage Images ---')
        gallery = GalleryImage.objects.filter(image__isnull=False).exclude(image='')
        for img in gallery:
            if img.image:
                image_path = os.path.join(settings.MEDIA_ROOT, img.image.name)
                if os.path.exists(image_path):
                    try:
                        with open(image_path, 'rb') as f:
                            url = upload_image(f, img.image.name)
                        if url:
                            self.stdout.write(self.style.SUCCESS(f'✓ {img.title or img.image.name}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'✗ {img.title}: Upload returned None'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'✗ {img.title}: {e}'))
                else:
                    self.stdout.write(self.style.WARNING(f'- {img.title}: File not found ({image_path})'))

        self.stdout.write(self.style.SUCCESS('\nUpload complete!'))
