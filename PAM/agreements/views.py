from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from .models import Phone, Agreement, PhoneHistory, PhoneAssignment
from accounts.models import CustomUser
from sales.models import SalesTransaction
from datetime import datetime
import base64
from io import BytesIO


@login_required
def phone_list_view(request):
    """List all phones with filtering and pagination"""
    # Managers see all phones, sellers see only their phones
    if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'manager'):
        phones = Phone.objects.all().select_related('current_owner').order_by('-created_at')
    else:
        phones = Phone.objects.filter(current_owner=request.user).select_related('current_owner').order_by('-created_at')
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        phones = phones.filter(status=status)
    
    owner_id = request.GET.get('owner')
    if owner_id:
        phones = phones.filter(current_owner_id=owner_id)
    
    search = request.GET.get('search')
    if search:
        phones = phones.filter(
            Q(imei_number__icontains=search) |
            Q(serial_number__icontains=search) |
            Q(brand__icontains=search) |
            Q(model__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(phones, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all sellers for filter dropdown
    sellers = CustomUser.objects.filter(role='seller', is_suspended=False)
    
    context = {
        'phones': page_obj,
        'sellers': sellers,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'agreements/phone_list.html', context)


@login_required
def phone_detail_view(request, pk):
    """View phone details with history"""
    phone = get_object_or_404(Phone, pk=pk)
    
    context = {
        'phone': phone,
    }
    
    return render(request, 'agreements/phone_detail.html', context)


@login_required
def phone_create_view(request):
    """Create a new phone"""
    if request.method == 'POST':
        try:
            phone = Phone.objects.create(
                brand=request.POST.get('brand'),
                model=request.POST.get('model'),
                imei_number=request.POST.get('imei_number'),
                serial_number=request.POST.get('serial_number'),
                color=request.POST.get('color'),
                storage_capacity=request.POST.get('storage_capacity'),
                purchase_price=request.POST.get('purchase_price') or None,
                current_owner=request.user,
                status='available',
                notes=request.POST.get('notes', '')
            )
            
            # Create history entry
            PhoneHistory.objects.create(
                phone=phone,
                action='created',
                description=f'Phone added to inventory by {request.user.get_full_name()}',
                performed_by=request.user
            )
            
            messages.success(request, 'Phone added successfully!')
            return redirect('phone_detail', pk=phone.pk)
            
        except Exception as e:
            messages.error(request, f'Error adding phone: {str(e)}')
    
    return render(request, 'agreements/phone_form.html')


@login_required
def phone_update_view(request, pk):
    """Update phone details"""
    phone = get_object_or_404(Phone, pk=pk)
    
    # Check permission
    if not (request.user == phone.current_owner or request.user.is_manager() or request.user.is_superuser):
        messages.error(request, 'You do not have permission to edit this phone.')
        return redirect('phone_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            phone.brand = request.POST.get('brand')
            phone.model = request.POST.get('model')
            phone.color = request.POST.get('color')
            phone.storage_capacity = request.POST.get('storage_capacity')
            phone.purchase_price = request.POST.get('purchase_price') or None
            phone.notes = request.POST.get('notes', '')
            phone.save()
            
            PhoneHistory.objects.create(
                phone=phone,
                action='updated',
                description=f'Phone information updated by {request.user.get_full_name()}',
                performed_by=request.user
            )
            
            messages.success(request, 'Phone updated successfully!')
            return redirect('phone_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error updating phone: {str(e)}')
    
    context = {'phone': phone}
    return render(request, 'agreements/phone_form.html', context)


@login_required
def agreement_list_view(request):
    """List all agreements with filtering"""
    agreements = Agreement.objects.all().select_related('phone', 'seller').order_by('-created_at')
    
    # Apply filters
    agreement_type = request.GET.get('type')
    if agreement_type:
        agreements = agreements.filter(agreement_type=agreement_type)
    
    search = request.GET.get('search')
    if search:
        agreements = agreements.filter(
            Q(agreement_number__icontains=search) |
            Q(buyer_name__icontains=search)
        )
    
    date_filter = request.GET.get('date')
    if date_filter:
        agreements = agreements.filter(created_at__date=date_filter)
    
    # Pagination
    paginator = Paginator(agreements, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'agreements': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'agreements/agreement_list.html', context)


@login_required
def agreement_detail_view(request, pk):
    """View agreement details"""
    agreement = get_object_or_404(Agreement, pk=pk)
    
    context = {
        'agreement': agreement,
    }
    
    return render(request, 'agreements/agreement_detail.html', context)


@login_required
def agreement_create_view(request):
    """Create a new agreement"""
    if request.method == 'POST':
        try:
            phone_id = request.POST.get('phone')
            phone = get_object_or_404(Phone, pk=phone_id)
            
            # Validate phone is available
            if phone.status != 'available':
                messages.error(request, 'Selected phone is not available.')
                return redirect('agreement_create')
            
            # Create agreement
            agreement = Agreement.objects.create(
                phone=phone,
                seller=request.user,
                agreement_type=request.POST.get('agreement_type'),
                buyer_name=request.POST.get('buyer_name'),
                buyer_phone=request.POST.get('buyer_phone'),
                buyer_email=request.POST.get('buyer_email', ''),
                buyer_address=request.POST.get('buyer_address'),
                buyer_id_type=request.POST.get('buyer_id_type'),
                buyer_id_number=request.POST.get('buyer_id_number'),
                agreed_price=request.POST.get('agreed_price'),
                payment_method=request.POST.get('payment_method'),
                agreement_duration_days=request.POST.get('agreement_duration_days') or None,
                terms_and_conditions=request.POST.get('terms_and_conditions', ''),
                seller_signature_base64=request.POST.get('seller_signature_base64'),
                buyer_signature_base64=request.POST.get('buyer_signature_base64'),
                id_document_photo=request.POST.get('id_document_photo', ''),
                passport_photo=request.POST.get('passport_photo', '')
            )
            
            # Update phone status
            if agreement.agreement_type == 'sell':
                phone.status = 'sold'
                phone.save()
                
                # Create phone history
                PhoneHistory.objects.create(
                    phone=phone,
                    action='sold',
                    description=f'Phone sold to {agreement.buyer_name} via agreement {agreement.agreement_number}',
                    performed_by=request.user
                )
                
                # Create sales transaction
                from decimal import Decimal
                sale_price = Decimal(str(agreement.agreed_price))
                cost_price = Decimal(str(phone.purchase_price or 0))
                profit = sale_price - cost_price
                
                SalesTransaction.objects.create(
                    transaction_id=f'TXN-{agreement.id}',
                    seller=request.user,
                    phone=phone,
                    agreement=agreement,
                    customer_name=agreement.buyer_name,
                    customer_phone=agreement.buyer_phone,
                    customer_email=agreement.buyer_email or '',
                    sale_price=sale_price,
                    cost_price=cost_price,
                    profit=profit,
                    commission_rate=Decimal('10.00'),  # Default 10%
                    payment_method=agreement.payment_method,
                    status='completed'
                )
            
            messages.success(request, f'Agreement {agreement.agreement_number} created successfully!')
            return redirect('agreement_detail', pk=agreement.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating agreement: {str(e)}')
    
    # GET request - show form
    available_phones = Phone.objects.filter(status='available', current_owner=request.user)
    selected_phone = request.GET.get('phone')
    
    context = {
        'available_phones': available_phones,
        'selected_phone': int(selected_phone) if selected_phone else None,
    }
    
    return render(request, 'agreements/agreement_create.html', context)


@login_required
def agreement_pdf_view(request, pk):
    """Generate PDF for agreement"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from io import BytesIO
    from django.conf import settings
    import os
    
    agreement = get_object_or_404(Agreement, pk=pk)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Agreement_{agreement.id}_{agreement.created_at.strftime("%Y%m%d")}.pdf"'
    
    # Define header/footer function with logo
    def add_header_footer(canvas, doc):
        canvas.saveState()
        
        # Header section with border
        canvas.setStrokeColor(colors.HexColor('#2563eb'))
        canvas.setLineWidth(2)
        canvas.line(50, letter[1] - 85, letter[0] - 50, letter[1] - 85)
        
        # Header with logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, 50, letter[1] - 80, width=0.8*inch, height=0.8*inch, preserveAspectRatio=True, mask='auto')
        
        # Company name - Right aligned
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(letter[0] - 50, letter[1] - 45, "PHONE AGREEMENT")
        canvas.setFont('Helvetica', 11)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(letter[0] - 50, letter[1] - 60, "MANAGEMENT SYSTEM")
        
        # Agreement reference in header
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(letter[0] - 50, letter[1] - 75, f"Ref: AGR-{str(agreement.id).zfill(6)}")
        
        # Footer with border
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)
        canvas.line(50, 45, letter[0] - 50, 45)
        
        # Footer text
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.black)
        canvas.drawString(50, 32, "This is a legally binding agreement")
        canvas.drawCentredString(letter[0] / 2, 32, f"Generated: {agreement.created_at.strftime('%B %d, %Y')}")
        canvas.drawRightString(letter[0] - 50, 32, f"Page {doc.page}")
        
        canvas.restoreState()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=50, leftMargin=50, 
                           topMargin=100, bottomMargin=50)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        spaceAfter=3,
        spaceBefore=3,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=0,
        spaceBefore=0
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=8
    )
    
    # Title - changes based on agreement type
    title_text = "PHONE PURCHASE AGREEMENT" if agreement.agreement_type == 'buy' else "PHONE SALES AGREEMENT"
    title = Paragraph(title_text, title_style)
    elements.append(title)
    subtitle = Paragraph(f"Agreement Reference: AGR-{str(agreement.id).zfill(6)} | Date: {agreement.created_at.strftime('%B %d, %Y')}", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 3))
    
    # Combined information table - All 4 sections in one professional table
    # Role labels change based on agreement type
    if agreement.agreement_type == 'buy':
        # Dealer is BUYING from customer (customer is SELLER)
        dealer_role = "DEALER (BUYER)"
        customer_role = "CUSTOMER (SELLER)"
    else:
        # Dealer is SELLING to customer (customer is BUYER)
        dealer_role = "DEALER (SELLER)"
        customer_role = "CUSTOMER (BUYER)"
    
    main_data = [
        # Section headers
        [Paragraph(f"<b>1. {dealer_role}</b>", section_style), '', 
         Paragraph(f"<b>2. {customer_role}</b>", section_style), ''],
        # Data rows
        ['Full Name:', agreement.seller.get_full_name(), 
         'Full Name:', agreement.customer_name],
        ['National ID:', agreement.seller.national_id or 'N/A', 
         'National ID:', agreement.customer_national_id],
        ['Phone Number:', agreement.seller.phone_number or 'N/A', 
         'Phone Number:', agreement.customer_phone],
        ['Address/Location:', agreement.seller.address or 'N/A', 
         'Address/Location:', agreement.customer_address],
        
        # Phone Details Section
        [Paragraph("<b>3. PHONE DETAILS</b>", section_style), '', 
         Paragraph("<b>4. AGREEMENT DETAILS</b>", section_style), ''],
        ['Brand:', agreement.phone.brand, 
         'Date of Transaction:', agreement.created_at.strftime('%Y-%m-%d %H:%M')],
        ['Model:', agreement.phone.model, 
         'Location of Transaction:', agreement.seller.address or 'N/A'],
        ['IMEI Number:', agreement.phone.imei, 
         'Agreement Reference:', f'AGR-{str(agreement.id).zfill(6)}'],
        ['Serial Number:', agreement.phone.serial_number or 'N/A', '', ''],
        ['Condition:', agreement.phone.get_condition_display(), '', ''],
        ['Selling Price:', Paragraph(f"<b>RWF {agreement.price:,.2f}</b>", styles['Normal']), '', ''],
    ]
    
    main_table = Table(main_data, colWidths=[1.4*inch, 1.8*inch, 1.4*inch, 1.6*inch])
    main_table.setStyle(TableStyle([
        # Section headers style
        ('SPAN', (0, 0), (1, 0)),  # Seller header
        ('SPAN', (2, 0), (3, 0)),  # Customer header
        ('SPAN', (0, 5), (1, 5)),  # Phone details header
        ('SPAN', (2, 5), (3, 5)),  # Agreement details header
        ('BACKGROUND', (0, 0), (1, 0), colors.white),
        ('BACKGROUND', (2, 0), (3, 0), colors.white),
        ('BACKGROUND', (0, 5), (1, 5), colors.white),
        ('BACKGROUND', (2, 5), (3, 5), colors.white),
        
        # General styling
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 6))
    
    # Photos and Signatures section
    photo_sig_data = []
    photo_sig_row = []
    
    # ID Photo (Customer)
    if agreement.id_photo:
        try:
            # Use the path attribute of the FieldFile
            id_photo_path = agreement.id_photo.path
            if os.path.exists(id_photo_path):
                img = Image(id_photo_path, width=1.5*inch, height=1.5*inch, kind='proportional')
                photo_sig_row.append(img)
            else:
                photo_sig_row.append(Paragraph("<b>ID Photo</b><br/>(Not Available)", styles['Normal']))
        except Exception as e:
            photo_sig_row.append(Paragraph(f"<b>ID Photo</b><br/>(Error: {str(e)[:20]})", styles['Normal']))
    else:
        photo_sig_row.append(Paragraph("<b>ID Photo</b><br/>(Not Available)", styles['Normal']))
    
    # Passport Photo placeholder
    photo_sig_row.append(Paragraph("<b>Passport Photo</b><br/>(Placeholder)", styles['Normal']))
    
    photo_sig_data.append(photo_sig_row)
    photo_sig_data.append([Paragraph("<b>ID Photo</b>", styles['Normal']), 
                           Paragraph("<b>Passport Photo</b>", styles['Normal'])])
    
    # Signatures row
    sig_row = []
    
    # Seller Signature
    if agreement.seller.signature:
        try:
            seller_sig_path = agreement.seller.signature.path
            if os.path.exists(seller_sig_path):
                sig_img = Image(seller_sig_path, width=1.8*inch, height=0.8*inch, kind='proportional')
                sig_row.append(sig_img)
            else:
                sig_row.append('_' * 30)
        except Exception as e:
            sig_row.append('_' * 30)
    else:
        sig_row.append('_' * 30)
    
    # Customer Signature
    if agreement.signature_photo:
        try:
            customer_sig_path = agreement.signature_photo.path
            if os.path.exists(customer_sig_path):
                sig_img = Image(customer_sig_path, width=1.8*inch, height=0.8*inch, kind='proportional')
                sig_row.append(sig_img)
            else:
                sig_row.append('_' * 30)
        except Exception as e:
            sig_row.append('_' * 30)
    else:
        sig_row.append('_' * 30)
    
    photo_sig_data.append(sig_row)
    photo_sig_data.append([Paragraph("<b>Seller Signature</b>", styles['Normal']), 
                           Paragraph("<b>Customer Signature</b>", styles['Normal'])])
    
    photo_sig_table = Table(photo_sig_data, colWidths=[3.3*inch, 3.3*inch])
    photo_sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(photo_sig_table)
    elements.append(Spacer(1, 5))
    
    # Terms & Conditions Box
    terms_title = Paragraph(
        "<b>TERMS AND CONDITIONS</b>",
        ParagraphStyle('TermsTitle', parent=styles['Normal'], fontSize=8, 
                      fontName='Helvetica-Bold', textColor=colors.black, 
                      alignment=TA_CENTER, spaceAfter=3)
    )
    
    disclaimer_text = (
        "I, the undersigned buyer, confirm that I have legally purchased the phone described above from the registered dealer. "
        "I understand and acknowledge that:<br/><br/>"
        "• This agreement constitutes a binding contract between the parties mentioned above.<br/>"
        "• All information provided is accurate and complete to the best of my knowledge.<br/>"
        "• This agreement may be used for verification by relevant authorities and law enforcement.<br/>"
        "• The phone has been inspected and is accepted in the condition described above.<br/>"
        "• Any disputes arising from this agreement shall be resolved in accordance with applicable law."
    )
    
    disclaimer = Paragraph(
        disclaimer_text,
        ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=6, 
                      textColor=colors.black, alignment=TA_JUSTIFY,
                      leftIndent=8, rightIndent=8, spaceAfter=3)
    )
    
    terms_data = [[terms_title], [disclaimer]]
    terms_table = Table(terms_data, colWidths=[6.6*inch])
    terms_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.white),
        ('BACKGROUND', (0, 1), (0, 1), colors.white),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (0, 0), 3),
        ('BOTTOMPADDING', (0, 0), (0, 0), 3),
        ('TOPPADDING', (0, 1), (0, 1), 4),
        ('BOTTOMPADDING', (0, 1), (0, 1), 4),
    ]))
    elements.append(terms_table)
    
    # Build PDF with header/footer
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@login_required
def phone_assign_view(request, pk):
    """Assign phone to another seller"""
    phone = get_object_or_404(Phone, pk=pk)
    
    # Check permission
    if phone.current_owner != request.user and not request.user.is_manager():
        messages.error(request, 'You do not have permission to assign this phone.')
        return redirect('phone_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            to_seller_id = request.POST.get('to_seller')
            to_seller = get_object_or_404(CustomUser, pk=to_seller_id, role='seller')
            
            # Create assignment
            assignment = PhoneAssignment.objects.create(
                phone=phone,
                from_seller=request.user,
                to_seller=to_seller,
                reason=request.POST.get('reason', '')
            )
            
            # Update phone status
            phone.status = 'assigned'
            phone.save()
            
            # Create history
            PhoneHistory.objects.create(
                phone=phone,
                action='assigned',
                description=f'Phone assigned to {to_seller.get_full_name()}',
                performed_by=request.user
            )
            
            messages.success(request, f'Phone assigned to {to_seller.get_full_name()} successfully!')
            return redirect('phone_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error assigning phone: {str(e)}')
    
    # GET request
    sellers = CustomUser.objects.filter(role='seller', is_suspended=False).exclude(id=request.user.id)
    
    context = {
        'phone': phone,
        'sellers': sellers,
    }
    
    return render(request, 'agreements/phone_assign.html', context)


@login_required
def buy_phone_view(request):
    """
    Combined view: Buy a phone and create buying agreement.
    Creates both phone record and buying agreement in one step.
    """
    # Check profile completion
    if not all([request.user.first_name, request.user.last_name, request.user.signature, 
                request.user.phone_number, request.user.address, request.user.national_id]):
        messages.warning(request, 'Please complete your profile before creating agreements.')
        return redirect('profile')
    
    if request.method == 'POST':
        try:
            # Create phone record
            phone = Phone.objects.create(
                imei=request.POST.get('imei_number'),
                serial_number=request.POST.get('serial_number'),
                brand=request.POST.get('brand'),
                model=request.POST.get('model'),
                color=request.POST.get('color'),
                condition=request.POST.get('condition', 'used'),
                purchase_price=request.POST.get('purchase_price'),
                status='available',
                current_owner=request.user
            )
            
            # Handle webcam image (supplier ID photo) and signature photo
            supplier_id_photo = request.POST.get('supplier_id_photo')
            supplier_signature_photo = request.POST.get('supplier_signature_photo')
            
            # Create buying agreement
            agreement = Agreement.objects.create(
                phone=phone,
                seller=request.user,
                agreement_type='buy',
                customer_name=request.POST.get('supplier_name'),
                customer_national_id=request.POST.get('supplier_id'),
                customer_phone=request.POST.get('supplier_phone'),
                customer_address=request.POST.get('supplier_address'),
                price=request.POST.get('purchase_price'),
                notes=request.POST.get('notes', '')
            )
            
            # Save supplier ID photo if provided
            if supplier_id_photo and supplier_id_photo.startswith('data:image'):
                format, imgstr = supplier_id_photo.split(';base64,')
                ext = format.split('/')[-1]
                data = base64.b64decode(imgstr)
                agreement.id_photo.save(f'supplier_id_{agreement.id}.{ext}', BytesIO(data), save=True)
            
            # Save supplier signature photo if provided
            if supplier_signature_photo and supplier_signature_photo.startswith('data:image'):
                format, imgstr = supplier_signature_photo.split(';base64,')
                ext = format.split('/')[-1]
                data = base64.b64decode(imgstr)
                agreement.signature_photo.save(f'supplier_sig_{agreement.id}.{ext}', BytesIO(data), save=True)
            
            # Create history
            PhoneHistory.objects.create(
                phone=phone,
                action='buy',
                from_user=request.user,
                agreement=agreement,
                notes=f'Phone purchased from {agreement.customer_name}'
            )
            
            messages.success(request, 'Phone purchased and agreement created successfully!')
            return redirect('agreement_detail', pk=agreement.id)
            
        except Exception as e:
            messages.error(request, f'Error creating purchase: {str(e)}')
    
    return render(request, 'agreements/buy_phone.html')


@login_required
def sell_phone_view(request, phone_id):
    """
    Sell an existing phone (create selling agreement).
    Only available phones can be sold.
    """
    phone = get_object_or_404(Phone, pk=phone_id)
    
    # Check if phone is available for sale
    if phone.status != 'available':
        messages.error(request, 'This phone is not available for sale.')
        return redirect('phone_detail', pk=phone_id)
    
    # Check profile completion
    if not all([request.user.first_name, request.user.last_name, request.user.signature, 
                request.user.phone_number, request.user.address, request.user.national_id]):
        messages.warning(request, 'Please complete your profile before creating agreements.')
        return redirect('profile')
    
    if request.method == 'POST':
        try:
            # Get buyer ID photo and signature photo
            buyer_id_photo = request.POST.get('buyer_id_photo')
            buyer_signature_photo = request.POST.get('buyer_signature_photo')
            
            # Create selling agreement
            agreement = Agreement.objects.create(
                phone=phone,
                seller=request.user,
                agreement_type='sell',
                customer_name=request.POST.get('buyer_name'),
                customer_national_id=request.POST.get('buyer_id'),
                customer_phone=request.POST.get('buyer_phone'),
                customer_address=request.POST.get('buyer_address'),
                price=request.POST.get('agreed_price'),
                notes=request.POST.get('notes', '')
            )
            
            # Save buyer ID photo if provided
            if buyer_id_photo and buyer_id_photo.startswith('data:image'):
                format, imgstr = buyer_id_photo.split(';base64,')
                ext = format.split('/')[-1]
                data = base64.b64decode(imgstr)
                agreement.id_photo.save(f'buyer_id_{agreement.id}.{ext}', BytesIO(data), save=True)
            
            # Save buyer signature photo
            if buyer_signature_photo and buyer_signature_photo.startswith('data:image'):
                format, imgstr = buyer_signature_photo.split(';base64,')
                ext = format.split('/')[-1]
                data = base64.b64decode(imgstr)
                agreement.signature_photo.save(f'buyer_sig_{agreement.id}.{ext}', BytesIO(data), save=True)
            
            # Update phone status
            phone.status = 'sold'
            phone.save()
            
            # Create sales transaction
            from decimal import Decimal
            sale_price = Decimal(request.POST.get('agreed_price'))
            cost_price = phone.purchase_price or Decimal('0')
            profit = sale_price - cost_price
            SalesTransaction.objects.create(
                agreement=agreement,
                seller=request.user,
                phone=phone,
                customer_name=request.POST.get('buyer_name'),
                customer_phone=request.POST.get('buyer_phone'),
                customer_email=request.POST.get('buyer_email', ''),
                sale_price=sale_price,
                cost_price=cost_price,
                profit=profit,
                payment_method=request.POST.get('payment_method', 'cash'),
                transaction_id=f'TXN-{agreement.id}'
            )
            
            # Create history
            PhoneHistory.objects.create(
                phone=phone,
                action='sell',
                from_user=request.user,
                agreement=agreement,
                notes=f'Phone sold to {agreement.customer_name}'
            )
            
            messages.success(request, 'Phone sold and agreement created successfully!')
            return redirect('agreement_detail', pk=agreement.id)
            
        except Exception as e:
            messages.error(request, f'Error creating sale: {str(e)}')
    
    context = {
        'phone': phone,
    }
    
    return render(request, 'agreements/sell_phone.html', context)


@login_required
def assign_phone_view(request, phone_id):
    """Assign a phone to another seller"""
    phone = get_object_or_404(Phone, id=phone_id, current_owner=request.user)
    
    if phone.status != 'available':
        messages.error(request, 'Only available phones can be assigned.')
        return redirect('phone_list')
    
    if request.method == 'POST':
        to_seller_id = request.POST.get('to_seller')
        message = request.POST.get('message', '')
        
        try:
            to_seller = CustomUser.objects.get(id=to_seller_id, role='seller', is_suspended=False)
            
            if to_seller == request.user:
                messages.error(request, 'You cannot assign a phone to yourself.')
                return redirect('assign_phone', phone_id=phone_id)
            
            # Create assignment request
            from .models import PhoneAssignment
            assignment = PhoneAssignment.objects.create(
                phone=phone,
                from_seller=request.user,
                to_seller=to_seller,
                message=message
            )
            
            # Mark phone as assigned
            phone.status = 'assigned'
            phone.save()
            
            messages.success(request, f'Assignment request sent to {to_seller.get_full_name()}')
            return redirect('phone_list')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid seller selected.')
        except Exception as e:
            messages.error(request, f'Error creating assignment: {str(e)}')
    
    # Get all active sellers except current user
    sellers = CustomUser.objects.filter(
        role='seller',
        is_suspended=False
    ).exclude(id=request.user.id)
    
    context = {
        'phone': phone,
        'sellers': sellers,
    }
    
    return render(request, 'agreements/assign_phone.html', context)


@login_required
def assignment_list_view(request):
    """View all assignments (sent and received)"""
    from .models import PhoneAssignment
    
    # Get assignments sent by current user
    sent_assignments = PhoneAssignment.objects.filter(
        from_seller=request.user
    ).select_related('phone', 'to_seller').order_by('-created_at')
    
    # Get assignments received by current user
    received_assignments = PhoneAssignment.objects.filter(
        to_seller=request.user
    ).select_related('phone', 'from_seller').order_by('-created_at')
    
    context = {
        'sent_assignments': sent_assignments,
        'received_assignments': received_assignments,
    }
    
    return render(request, 'agreements/assignment_list.html', context)


@login_required
def approve_assignment_view(request, assignment_id):
    """Approve a phone assignment"""
    from .models import PhoneAssignment
    
    assignment = get_object_or_404(
        PhoneAssignment,
        id=assignment_id,
        to_seller=request.user,
        status='pending'
    )
    
    try:
        assignment.approve()
        messages.success(request, f'Assignment approved! {assignment.phone.brand} {assignment.phone.model} is now in your inventory.')
    except Exception as e:
        messages.error(request, f'Error approving assignment: {str(e)}')
    
    return redirect('assignment_list')


@login_required
def reject_assignment_view(request, assignment_id):
    """Reject a phone assignment"""
    from .models import PhoneAssignment
    
    assignment = get_object_or_404(
        PhoneAssignment,
        id=assignment_id,
        to_seller=request.user,
        status='pending'
    )
    
    try:
        assignment.reject()
        messages.info(request, f'Assignment rejected. {assignment.phone.brand} {assignment.phone.model} returned to {assignment.from_seller.get_full_name()}.')
    except Exception as e:
        messages.error(request, f'Error rejecting assignment: {str(e)}')
    
    return redirect('assignment_list')
