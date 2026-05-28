from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from .models import Product, ColorVariant, GalleryImage, RoofType
from .forms import ContactForm
from django.core.paginator import Paginator

# Static/simple views
def home(request):
    return render(request, 'index.html', {'current_page': 'home'})


def gallery(request):
    images_qs = GalleryImage.objects.all().order_by('order', '-uploaded_at')
    paginator = Paginator(images_qs, 12)  # 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'gallery.html', {'page_obj': page_obj, 'current_page': 'gallery'})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            messages.success(request, 'Thanks! Your request has been received. We will reply within 24 hours.')
            try:
                send_mail(
                    subject=f'New contact request from {contact_message.name}',
                    message=f'Name: {contact_message.name}\nEmail: {contact_message.email}\nPhone: {contact_message.phone}\n\nMessage:\n{contact_message.message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True,
                )
            except Exception:
                pass
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'current_page': 'contact', 'form': form})


def visualizer(request):
    roof_types = RoofType.objects.order_by('name')
    color_variants = ColorVariant.objects.order_by('name')
    roof_types_data = [{'slug': roof_type.slug, 'name': roof_type.name} for roof_type in roof_types]
    color_variants_data = [
        {'slug': color.slug, 'name': color.name, 'hex_code': color.hex_code or '#ccc'}
        for color in color_variants
    ]
    return render(request, 'visualizer.html', {
        'current_page': 'visualizer',
        'roof_types': roof_types,
        'color_variants': color_variants,
        'roof_types_data': roof_types_data,
        'color_variants_data': color_variants_data,
    }) 


def about(request):
    return render(request, 'about.html', {'current_page': 'about'})


# Product list view: fetches products dynamically from the database
def products(request):
    products = Product.objects.select_related('roof_type').prefetch_related('images', 'color_variants').all()
    roof_type_slug = request.GET.get('roof_type')
    color_slug = request.GET.get('color')
    search = request.GET.get('q')

    if roof_type_slug:
        products = products.filter(roof_type__slug=roof_type_slug)
    if color_slug:
        products = products.filter(color_variants__slug=color_slug)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))

    products = products.distinct()
    roof_types = RoofType.objects.order_by('name')
    color_variants = ColorVariant.objects.order_by('name')

    featured_products = Product.objects.filter(featured=True).select_related('roof_type').prefetch_related('images', 'color_variants')
    context = {
        'products': products,
        'featured_products': featured_products,
        'roof_types': roof_types,
        'color_variants': color_variants,
        'active_roof_type': roof_type_slug,
        'active_color': color_slug,
        'search_query': search,
        'current_page': 'products'
    }
    return render(request, 'products.html', context)


# Product detail view: shows a single product
def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('roof_type').prefetch_related('images', 'color_variants'), slug=slug)
    color_variants = product.color_variants.all()
    context = {
        'product': product,
        'color_variants': color_variants,
        'current_page': 'products',
    }
    return render(request, 'product_detail.html', context)


