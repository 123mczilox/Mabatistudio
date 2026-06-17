import math
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
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
from .forms import ContactForm, QuoteRequestForm
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


def robots_txt(request):
    content = """User-agent: *
Allow: /

Sitemap: https://mabatihubkenya.co.ke/sitemap.xml"""
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    base_url = request.build_absolute_uri('/')
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    static_paths = [
        '',
        'gallery/',
        'contact/',
        'products/',
        'roof-calculator/',
        'about/',
    ]

    urls = [
        f"{base_url}/{path}" if path else f"{base_url}/"
        for path in static_paths
    ]

    products = Product.objects.all()
    for product in products:
        urls.append(f"{base_url}{product.get_absolute_url()}")

    xml_urls = [
        '  <url>\n    <loc>{}</loc>\n  </url>'.format(url)
        for url in urls
    ]
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml_content += '\n'.join(xml_urls)
    xml_content += '\n</urlset>'

    return HttpResponse(xml_content, content_type='application/xml')


def parse_decimal(value, default=Decimal('0')):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return default


def calculate_estimate_values(data, profile=None):
    length = parse_decimal(data.get('length', '0'))
    width = parse_decimal(data.get('width', '0'))
    eaves = parse_decimal(data.get('eaves', '0'))
    pitch = parse_decimal(data.get('pitch', '0'))
    calculation_method = data.get('calculationMethod', 'dimensions')
    direct_area = parse_decimal(data.get('directArea', '0'))
    roof_type = data.get('roofType', 'Gable Roof')

    if calculation_method == 'direct_area':
        roof_area = direct_area
    else:
        plan_length = float(length + eaves * 2)
        plan_width = float(width + eaves * 2)
        footprint = plan_length * plan_width
        slope_multiplier = 1 / math.cos(math.radians(float(pitch))) if float(pitch) > 0 else 1
        roof_area = Decimal(str(footprint * get_type_factor(roof_type) * slope_multiplier))

    sheet_total_width = parse_decimal(data.get('sheetTotalWidth', '0'))
    sheet_total_length = parse_decimal(data.get('sheetTotalLength', '0'))
    side_lap = parse_decimal(data.get('sideLap', '0'))
    end_lap = parse_decimal(data.get('endLap', '0'))
    end_overhang = parse_decimal(data.get('endOverhang', '0'))
    sheet_price = parse_decimal(data.get('sheetPrice', '0'))
    ridge_price = parse_decimal(data.get('ridgePrice', '0'))
    screw_price = parse_decimal(data.get('screwPrice', '0'))
    nail_price = parse_decimal(data.get('nailPrice', '0'))
    timber_price = parse_decimal(data.get('timberPrice', '0'))
    labour_cost = parse_decimal(data.get('labourCost', '0'))
    rainfall = parse_decimal(data.get('rainfall', '0'))
    include_screws = data.get('includeScrews') == 'on'
    include_nails = data.get('includeNails') == 'on'
    include_timber = data.get('includeTimber') == 'on'
    include_rainwater = data.get('includeRainwater') == 'on'

    effective_sheet_area = Decimal('0')
    if sheet_total_width > 0 and sheet_total_length > 0:
        effective_sheet_width = max(Decimal('0'), sheet_total_width - side_lap)
        effective_sheet_length = max(Decimal('0'), sheet_total_length - end_lap - end_overhang)
        effective_sheet_area = effective_sheet_width * effective_sheet_length

    if effective_sheet_area <= 0:
        if profile and profile.cover_width:
            effective_sheet_area = parse_decimal(profile.cover_width)
        else:
            effective_sheet_area = Decimal('1')

    base_sheets = float(roof_area) / float(effective_sheet_area) if effective_sheet_area else 0
    wastage = get_wastage(roof_type)
    recommended_sheets = max(0, int(math.ceil(base_sheets * (1 + wastage))))
    ridge_length = get_ridge_length(roof_type, float(length), float(width))
    ridge_caps = max(0, int(math.ceil(ridge_length / 2)))
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

    return {
        'roof_area': roof_area,
        'recommended_sheets': recommended_sheets,
        'ridge_caps': ridge_caps,
        'screws': screws,
        'nails': nails,
        'timber_length': timber_length,
        'rainwater_litres': rainwater_litres,
        'material_cost': material_cost,
        'labour_cost': labour_cost,
        'grand_total': grand_total,
    }


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
    products = Product.objects.order_by('name').prefetch_related('gauge_variants__gauge')

    initial_data = {
        'length': '50',
        'width': '100',
        'roofType': 'Gable Roof',
        'pitch': '25',
        'profile': str(profiles.first().pk) if profiles.exists() else '',
        'product': '',
        'productVariant': '',
        'gauge': str(gauges.first().pk) if gauges.exists() else '',
        'color': 'Charcoal Grey',
        'calculationMethod': 'dimensions',
        'directArea': '0',
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
        'eaves': '0.10',
        'sheetTotalWidth': '1.05',
        'sheetTotalLength': '3.05',
        'sideLap': '0.05',
        'endLap': '0.10',
        'endOverhang': '0.10',
    }

    if request.GET:
        for key in list(initial_data.keys()):
            if key in request.GET:
                initial_data[key] = request.GET.get(key, initial_data[key])
        for checkbox in ['includeScrews', 'includeNails', 'includeTimber', 'includeRainwater']:
            initial_data[checkbox] = 'on' if request.GET.get(checkbox) == 'on' else 'off'

    roof_types = ['Gable Roof', 'Hip Roof', 'Mono-Pitch Roof', 'Flat Roof']
    pitch_options = ['15', '20', '25', '30', '35', '40']

    return render(request, 'roof_calculator.html', {
        'current_page': 'roof_calculator',
        'profiles': profiles,
        'gauges': gauges,
        'products': products,
        'color_variants': color_variants,
        'initial_data': initial_data,
        'roof_types': roof_types,
        'pitch_options': pitch_options,
    })


def request_quote(request):
    profiles = RoofingProfile.objects.order_by('order', 'name')
    gauges = RoofGauge.objects.order_by('order', 'name')
    products = Product.objects.order_by('name').prefetch_related('gauge_variants__gauge')

    default_data = {
        'length': '50',
        'width': '100',
        'roofType': 'Gable Roof',
        'pitch': '25',
        'profile': str(profiles.first().pk) if profiles.exists() else '',
        'product': '',
        'productVariant': '',
        'gauge': str(gauges.first().pk) if gauges.exists() else '',
        'color': 'Charcoal Grey',
        'calculationMethod': 'dimensions',
        'directArea': '0',
        'sheetPrice': '1800',
        'ridgePrice': '800',
        'screwPrice': '5',
        'nailPrice': '3',
        'timberPrice': '250',
        'labourCost': '25000',
        'rainfall': '1200',
        'includeScrews': 'off',
        'includeNails': 'off',
        'includeTimber': 'off',
        'includeRainwater': 'off',
        'eaves': '0.10',
        'sheetTotalWidth': '1.05',
        'sheetTotalLength': '3.05',
        'sideLap': '0.05',
        'endLap': '0.10',
        'endOverhang': '0.10',
    }

    hidden_data = default_data.copy()
    if request.method == 'GET' and request.GET:
        for key in hidden_data:
            if key in request.GET:
                hidden_data[key] = request.GET.get(key, hidden_data[key])
        for checkbox in ['includeScrews', 'includeNails', 'includeTimber', 'includeRainwater']:
            hidden_data[checkbox] = 'on' if request.GET.get(checkbox) == 'on' else 'off'

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        hidden_data.update({
            key: request.POST.get(key, hidden_data[key])
            for key in hidden_data
        })
        profile_id = request.POST.get('profile')
        profile = RoofingProfile.objects.filter(pk=profile_id).first() if profile_id else None
        estimate = calculate_estimate_values(hidden_data, profile=profile)

        if form.is_valid():
            quote = form.save(commit=False)
            quote.session_key = get_session_key(request)
            quote.calculation_method = request.POST.get('calculationMethod', 'dimensions')
            quote.roof_type = request.POST.get('roofType', 'Gable Roof')
            quote.profile = profile
            gauge_id = request.POST.get('gauge')
            quote.gauge = RoofGauge.objects.filter(pk=gauge_id).first() if gauge_id else None
            quote.color = request.POST.get('color', '').strip()
            quote.length = parse_decimal(request.POST.get('length', '0'))
            quote.width = parse_decimal(request.POST.get('width', '0'))
            quote.direct_area = parse_decimal(request.POST.get('directArea', '0'))
            quote.pitch = parse_decimal(request.POST.get('pitch', '0'))
            quote.include_screws = request.POST.get('includeScrews') == 'on'
            quote.include_nails = request.POST.get('includeNails') == 'on'
            quote.include_timber = request.POST.get('includeTimber') == 'on'
            quote.include_rainwater = request.POST.get('includeRainwater') == 'on'
            quote.rainfall = parse_decimal(request.POST.get('rainfall', '0'))
            quote.roof_area = estimate['roof_area']
            quote.recommended_sheets = estimate['recommended_sheets']
            quote.ridge_caps = estimate['ridge_caps']
            quote.screws = estimate['screws']
            quote.nails = estimate['nails']
            quote.timber_length = estimate['timber_length']
            quote.rainwater_litres = estimate['rainwater_litres']
            quote.eaves = parse_decimal(request.POST.get('eaves', '0'))
            quote.sheet_total_width = parse_decimal(request.POST.get('sheetTotalWidth', '0'))
            quote.sheet_total_length = parse_decimal(request.POST.get('sheetTotalLength', '0'))
            quote.side_lap = parse_decimal(request.POST.get('sideLap', '0'))
            quote.end_lap = parse_decimal(request.POST.get('endLap', '0'))
            quote.end_overhang = parse_decimal(request.POST.get('endOverhang', '0'))
            quote.sheet_price = parse_decimal(request.POST.get('sheetPrice', '0'))
            quote.ridge_price = parse_decimal(request.POST.get('ridgePrice', '0'))
            quote.screw_price = parse_decimal(request.POST.get('screwPrice', '0'))
            quote.nail_price = parse_decimal(request.POST.get('nailPrice', '0'))
            quote.timber_price = parse_decimal(request.POST.get('timberPrice', '0'))
            quote.labour_cost = parse_decimal(request.POST.get('labourCost', '0'))
            quote.material_cost = estimate['material_cost']
            quote.grand_total = estimate['grand_total']
            quote.status = 'requested'
            quote.save()
            return redirect('quote_confirmation', quote_number=quote.quote_number)
    else:
        form = QuoteRequestForm()
        profile_id = hidden_data.get('profile')
        profile = RoofingProfile.objects.filter(pk=profile_id).first() if profile_id else None
        estimate = calculate_estimate_values(hidden_data, profile=profile)

    return render(request, 'quote_request.html', {
        'current_page': 'roof_calculator',
        'form': form,
        'hidden_data': hidden_data,
        'estimate': estimate,
        'roof_types': ['Gable Roof', 'Hip Roof', 'Mono-Pitch Roof', 'Flat Roof'],
        'pitch_options': ['15', '20', '25', '30', '35', '40'],
    })


def quote_confirmation(request, quote_number):
    session_key = get_session_key(request)
    quote = get_object_or_404(RoofEstimate, quote_number=quote_number, session_key=session_key)
    return render(request, 'quote_confirmation.html', {
        'current_page': 'roof_calculator',
        'quote': quote,
    })


def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def about(request):
    return render(request, 'about.html', {'current_page': 'about'})


# Product list view: fetches products dynamically from the database
def products(request):
    products = Product.objects.select_related('product_type').prefetch_related('images', 'color_variants', 'gauge_variants__gauge').all()
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

    featured_products = Product.objects.filter(featured=True).select_related('product_type').prefetch_related('images', 'color_variants', 'gauge_variants__gauge')
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
    product = get_object_or_404(Product.objects.select_related('product_type').prefetch_related('images', 'color_variants', 'gauge_variants__gauge'), slug=slug)
    color_variants = product.color_variants.all()
    context = {
        'product': product,
        'color_variants': color_variants,
        'current_page': 'products',
    }
    return render(request, 'product_detail.html', context)


