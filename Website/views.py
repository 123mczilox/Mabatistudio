import math
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from .models import (
    Product,
    ColorVariant,
    GalleryImage,
    ProductType,
    RoofingProfile,
    RoofGauge,
    RoofEstimate,
)
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


def parse_decimal(value, default=Decimal('0')):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return default


def get_type_factor(roof_type):
    return {
        'Gable Roof': 1.00,
        'Hip Roof': 1.06,
        'Mono-Pitch Roof': 1.02,
        'Flat Roof': 1.00,
    }.get(roof_type, 1.00)


def get_wastage(roof_type):
    return 0.10 if roof_type in ['Hip Roof', 'Mono-Pitch Roof'] else 0.05


def get_timber_factor(roof_type):
    return {
        'Gable Roof': 0.36,
        'Hip Roof': 0.45,
        'Mono-Pitch Roof': 0.32,
        'Flat Roof': 0.28,
    }.get(roof_type, 0.35)


def get_ridge_length(roof_type, length, width):
    if not length or not width:
        return 0
    if roof_type == 'Hip Roof':
        return max(length, width) * 1.1
    if roof_type == 'Mono-Pitch Roof':
        return length
    if roof_type == 'Flat Roof':
        return 0
    return length


def roof_calculator(request):
    profiles = RoofingProfile.objects.order_by('order', 'name')
    gauges = RoofGauge.objects.order_by('order', 'name')
    color_variants = ColorVariant.objects.order_by('name')

    initial_data = {
        'length': '50',
        'width': '100',
        'roofType': 'Gable Roof',
        'pitch': '25',
        'profile': str(profiles.first().pk) if profiles.exists() else '',
        'gauge': str(gauges.first().pk) if gauges.exists() else '',
        'color': 'Charcoal Grey',
        'sheetPrice': '1800',
        'ridgePrice': '800',
        'screwPrice': '5',
        'nailPrice': '3',
        'timberPrice': '250',
        'labourCost': '25000',
        'rainfall': '1200',
        'includeScrews': 'on',
        'includeNails': 'on',
        'includeTimber': 'on',
        'includeRainwater': 'on',
    }
    quote_saved = None

    if request.method == 'POST':
        if not request.session.session_key:
            request.session.create()

        post_data = request.POST.dict()
        initial_data.update(post_data)

        profile = RoofingProfile.objects.filter(pk=request.POST.get('profile')).first()
        gauge = RoofGauge.objects.filter(pk=request.POST.get('gauge')).first()

        sheet_price = Decimal('0')
        if profile and gauge:
            sheet_price = (profile.default_sheet_price * gauge.price_multiplier) + gauge.additional_cost
            initial_data['sheetPrice'] = str(sheet_price)
        else:
            sheet_price = parse_decimal(request.POST.get('sheetPrice', '0'))

        ridge_price = parse_decimal(request.POST.get('ridgePrice', '0'))
        screw_price = parse_decimal(request.POST.get('screwPrice', '0'))
        nail_price = parse_decimal(request.POST.get('nailPrice', '0'))
        timber_price = parse_decimal(request.POST.get('timberPrice', '0'))
        labour_cost = parse_decimal(request.POST.get('labourCost', '0'))
        rainfall = parse_decimal(request.POST.get('rainfall', '0'))
        length = parse_decimal(request.POST.get('length', '0'))
        width = parse_decimal(request.POST.get('width', '0'))
        pitch = parse_decimal(request.POST.get('pitch', '0'))
        roof_type = request.POST.get('roofType', 'Gable Roof')
        color = request.POST.get('color', '').strip()
        include_screws = request.POST.get('includeScrews') == 'on'
        include_nails = request.POST.get('includeNails') == 'on'
        include_timber = request.POST.get('includeTimber') == 'on'
        include_rainwater = request.POST.get('includeRainwater') == 'on'

        footprint = float(length) * float(width)
        slope_multiplier = 1 / math.cos(math.radians(float(pitch))) if float(pitch) > 0 else 1
        roof_area = Decimal(str(footprint * get_type_factor(roof_type) * slope_multiplier))
        cover_width = float(profile.cover_width) if profile else 1.0
        base_sheets = float(roof_area) / cover_width if cover_width else 0
        recommended_sheets = max(0, int((base_sheets * (1 + get_wastage(roof_type))) // 1 + (1 if (base_sheets * (1 + get_wastage(roof_type))) % 1 else 0)))
        ridge_length = get_ridge_length(roof_type, float(length), float(width))
        ridge_caps = max(0, int((ridge_length / 2) // 1 + (1 if (ridge_length / 2) % 1 else 0)))
        screws = max(0, int(math.ceil(float(roof_area) * 9))) if include_screws else 0
        nails = max(0, int(math.ceil(float(roof_area) * 6))) if include_nails else 0
        timber_length = Decimal(str(math.ceil(float(roof_area) * get_timber_factor(roof_type)))) if include_timber else Decimal('0')
        rainwater_litres = Decimal(str(round(float(roof_area) * float(rainfall) * 0.8))) if include_rainwater else Decimal('0')

        material_cost = (Decimal(recommended_sheets) * sheet_price) + (Decimal(ridge_caps) * ridge_price)
        if include_screws:
            material_cost += Decimal(screws) * screw_price
        if include_nails:
            material_cost += Decimal(nails) * nail_price
        if include_timber:
            material_cost += timber_length * timber_price

        grand_total = material_cost + labour_cost

        quote_saved = RoofEstimate.objects.create(
            session_key=request.session.session_key,
            roof_type=roof_type,
            profile=profile,
            gauge=gauge,
            color=color,
            length=length,
            width=width,
            pitch=pitch,
            include_screws=include_screws,
            include_nails=include_nails,
            include_timber=include_timber,
            include_rainwater=include_rainwater,
            rainfall=rainfall,
            roof_area=roof_area,
            recommended_sheets=recommended_sheets,
            ridge_caps=ridge_caps,
            screws=screws,
            nails=nails,
            timber_length=timber_length,
            rainwater_litres=rainwater_litres,
            sheet_price=sheet_price,
            ridge_price=ridge_price,
            screw_price=screw_price,
            nail_price=nail_price,
            timber_price=timber_price,
            labour_cost=labour_cost,
            material_cost=material_cost,
            grand_total=grand_total,
        )

        messages.success(request, f'Official quote saved: {quote_saved.quote_number}')

    return render(request, 'roof_calculator.html', {
        'current_page': 'roof_calculator',
        'profiles': profiles,
        'gauges': gauges,
        'color_variants': color_variants,
        'initial_data': initial_data,
        'quote_saved': quote_saved,
    })


def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def quote_history(request):
    session_key = get_session_key(request)
    quotes = RoofEstimate.objects.filter(session_key=session_key).order_by('-created_at')
    return render(request, 'roof_history.html', {
        'current_page': 'history',
        'quotes': quotes,
    })


def quote_detail(request, quote_number):
    session_key = get_session_key(request)
    quote = get_object_or_404(RoofEstimate, quote_number=quote_number, session_key=session_key)
    return render(request, 'roof_estimate_detail.html', {
        'current_page': 'history',
        'quote': quote,
    })


def about(request):
    return render(request, 'about.html', {'current_page': 'about'})


# Product list view: fetches products dynamically from the database
def products(request):
    products = Product.objects.select_related('product_type').prefetch_related('images', 'color_variants').all()
    product_type_slug = request.GET.get('product_type')
    color_slug = request.GET.get('color')
    search = request.GET.get('q')

    if product_type_slug:
        products = products.filter(product_type__slug=product_type_slug)
    if color_slug:
        products = products.filter(color_variants__slug=color_slug)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))

    products = products.distinct()
    product_types = ProductType.objects.order_by('name')
    color_variants = ColorVariant.objects.order_by('name')

    featured_products = Product.objects.filter(featured=True).select_related('product_type').prefetch_related('images', 'color_variants')
    context = {
        'products': products,
        'featured_products': featured_products,
        'product_types': product_types,
        'color_variants': color_variants,
        'active_product_type': product_type_slug,
        'active_color': color_slug,
        'search_query': search,
        'current_page': 'products'
    }
    return render(request, 'products.html', context)


# Product detail view: shows a single product
def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('product_type').prefetch_related('images', 'color_variants'), slug=slug)
    color_variants = product.color_variants.all()
    context = {
        'product': product,
        'color_variants': color_variants,
        'current_page': 'products',
    }
    return render(request, 'product_detail.html', context)


