# PAM (Phone Agreement Management) - Copilot Instructions

## Project Overview
Django 5.2.4 application for phone retail businesses to manage complete transaction lifecycle from purchase to sale with legal documentation and audit trails.

**Business Context**: Phone dealers buy and sell phones (new/used), requiring legal agreements for each transaction. This system digitizes the paper-based process, prevents phone theft verification issues, and maintains complete audit trails for compliance.

**Key Features**:
- Dual-role system (Sellers and Managers)
- Complete inventory tracking (IMEI/serial number based)
- Digital agreement generation with document capture
- Webcam integration for ID/passport photos
- Digital signature capture via HTML5 canvas
- PDF generation for agreements and reports
- Phone assignment workflow between sellers
- Manager-controlled seller activation system
- Immutable audit trail via PhoneHistory

**User Roles**:
- **Sellers**: Front-line dealers who buy/sell phones, manage inventory, assign phones to peers
- **Managers**: Supervisors with system-wide access, seller management, and reporting capabilities

**Three-app architecture**:
- **accounts**: Custom user authentication, role-based access (CustomUser model with seller/manager roles, suspension system)
- **agreements**: Phone inventory, agreements, assignment workflow, PDF generation (Phone, Agreement, PhoneHistory, PhoneAssignment models)
- **sales**: Sales tracking, performance analytics, targets, customer management (SalesTransaction, SellerPerformance, SalesTarget, Customer models)

Project root: `PAM/` contains `manage.py` and project settings in `PAM/PAM/`

## Architecture & Structure

```
PAM/
├── manage.py                 # Django CLI entry point
├── db.sqlite3               # SQLite database (not in git)
├── media/                   # User-uploaded files (agreements/)
├── PAM/                     # Main project config
│   ├── settings.py         # Configuration (AUTH_USER_MODEL, MEDIA_ROOT)
│   ├── urls.py            # Root URL routing
│   └── wsgi.py/asgi.py    # WSGI/ASGI application
├── accounts/               # Authentication & User Management
│   ├── models.py          # CustomUser model (role, suspension fields)
│   ├── views.py           # Registration, login, logout, seller management
│   ├── middleware.py      # SuspensionMiddleware (checks is_suspended)
│   ├── admin.py           # CustomUser admin registration
│   ├── templates/         # Auth templates (login, register, hold)
│   └── migrations/        # User model migrations
├── agreements/            # Phone & Agreement Management
│   ├── models.py          # Phone, Agreement, PhoneHistory, PhoneAssignment
│   ├── views.py           # Phone operations, agreements, PDF generation
│   ├── admin.py           # Phone/Agreement admin registrations
│   ├── templates/         # Phone/agreement templates
│   │   └── agreements/   # phone_list.html, create_agreement.html, etc.
│   └── migrations/        # Agreement model migrations
└── sales/                 # Sales Tracking & Analytics
    ├── models.py          # SalesTransaction, SellerPerformance, SalesTarget, Customer
    ├── views.py           # Sales reports, analytics, dashboards
    ├── admin.py           # Sales admin registrations
    ├── templates/         # Sales-related templates
    └── migrations/        # Sales model migrations
```

**Critical Configuration** (`PAM/settings.py`):
```python
AUTH_USER_MODEL = 'accounts.CustomUser'  # Custom user in accounts app
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
LOGIN_URL = '/login/'

INSTALLED_APPS = [
    # ... Django apps ...
    'accounts',      # Must be before agreements (defines CustomUser)
    'agreements',    # Depends on accounts.CustomUser
    'sales',         # Sales tracking and analytics
]

MIDDLEWARE = [
    # ... standard Django middleware ...
    'accounts.middleware.SuspensionMiddleware',  # MUST be after AuthenticationMiddleware
]
```

## Development Workflow

### Essential Commands (run from `PAM/` directory)
```cmd
python manage.py runserver              :: Start dev server (localhost:8000)
python manage.py makemigrations         :: Generate migration files
python manage.py migrate                :: Apply database migrations
python manage.py createsuperuser        :: Create manager account (choose role='manager')
python manage.py shell                  :: Interactive Python shell with Django
python manage.py create_sample_data --sellers 3 --phones 10  :: Generate test data
python manage.py collectstatic          :: Collect static files (production)
```

**Critical Migration Workflow**:
1. Modify models in `agreements/models.py`
2. Run `makemigrations` (creates migration file)
3. Run `migrate` (applies to database)
4. **NEVER** edit migration files manually unless resolving conflicts

### Frontend Technologies
```html
<!-- Bootstrap 5 for styling -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

<!-- Signature Pad for digital signatures -->
<script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>

<!-- Webcam capture (native browser API) -->
<script>
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => video.srcObject = stream);
</script>
```

### Document Capture Implementation
**Webcam Capture Flow**:
1. User clicks "Start Camera" → `getUserMedia()` requests permission
2. Video stream displays in `<video>` element
3. Click "Capture" → draws video frame to `<canvas>`
4. `canvas.toDataURL('image/png')` → base64 string
5. Store in hidden `<input>` field
6. Submit form with base64 data
7. Backend `save_base64_image()` converts to file

**Signature Pad Flow**:
1. Initialize: `new SignaturePad(canvas)`
2. User draws signature
3. On submit: `signaturePad.toDataURL()` → base64 string
4. Backend saves to BOTH `signature` (TextField) and `signature_photo` (ImageField)

### Dependencies (requirements.txt)
```
Django==5.2.4
reportlab==4.4.4          # PDF generation
Pillow==11.3.0            # Image processing
djangorestframework==3.15.2
```

## Django-Specific Patterns

### Custom User Model Registration
```python
# PAM/settings.py
AUTH_USER_MODEL = 'accounts.CustomUser'  # Points to accounts app

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... other Django apps ...
    'accounts',      # MUST be listed before agreements
    'agreements',    # Depends on accounts.CustomUser
]
```
**Critical**: This must be set BEFORE initial migrations. The `accounts` app MUST be in INSTALLED_APPS before `agreements` since agreements depends on CustomUser.

### Cross-App Model References
```python
# agreements/models.py - Import CustomUser from accounts app
from django.db import models
from accounts.models import CustomUser

class Phone(models.Model):
    current_owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # ... other fields
```

### Admin Registration Pattern
```python
# accounts/admin.py
from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'role', 'is_suspended', 'phone_number']
    list_filter = ['role', 'is_suspended', 'is_staff']
    search_fields = ['username', 'email', 'phone_number', 'national_id']

# agreements/admin.py
from django.contrib import admin
from .models import Phone, Agreement, PhoneHistory

@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
### Model Best Practices
```python
# Use choices for fixed options
condition = models.CharField(max_length=10, choices=[
    ('new', 'New'), ('used', 'Used'), ('other', 'Other')
])

# Auto timestamps
created_at = models.DateTimeField(auto_now_add=True)  # Set once on creation
updated_at = models.DateTimeField(auto_now=True)      # Updates on every save

# Related names for reverse lookups
current_owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_phones')
# Access: user.owned_phones.all()

# Indexes for search performance
class Meta:
    indexes = [models.Index(fields=['imei', 'serial_number'])]
```

### Form Processing Pattern
```python
# agreements/views.py
from accounts.models import CustomUser

if request.method == 'POST':
    form = AgreementForm(request.POST, request.FILES)
    if form.is_valid():
        agreement = form.save(commit=False)  # Don't save yet
        agreement.seller = request.user       # Add current user
        
        # Process base64 images
        if request.POST.get('id_photo'):
            agreement.id_photo = save_base64_image(request.POST['id_photo'], 'id_photos')
        
        agreement.save()  # Now save
        messages.success(request, 'Agreement created successfully!')
        return redirect('agreement_detail', agreement_id=agreement.id)
```     agreement.seller = request.user       # Add current user
        
        # Process base64 images
        if request.POST.get('id_photo'):
            agreement.id_photo = save_base64_image(request.POST['id_photo'], 'id_photos')
        
        agreement.save()  # Now save
        messages.success(request, 'Agreement created successfully!')
        return redirect('agreement_detail', agreement_id=agreement.id)
```

## Critical Workflows & Patterns

### 1. Seller Registration & Auto-Suspension
```python
# accounts/views.py::register()
user = form.save(commit=False)
if user.role == 'seller':
    user.is_suspended = True
    user.suspended_reason = "Awaiting manager activation"
    user.suspended_at = timezone.now()
user.save()
```
**Middleware Check** (`accounts/middleware.py::SuspensionMiddleware`):
- On EVERY request: If `user.is_suspended=True` → redirect to `/hold/` (except `/logout/`)
- Managers activate sellers via `/sellers/<id>/manage/` endpoint (in accounts app)

### 2. Adding Phone to Inventory (Buy Agreement Flow)
```python
# agreements/views.py::add_phone() - Single transaction creates:
# 1. Phone record (status='available', current_owner=request.user)
# 2. Buy agreement with previous owner's documents
# 3. PhoneHistory entry (action='buy')

# Import CustomUser from accounts app
from accounts.models import CustomUser

# Frontend captures webcam images:
const idPhotoData = canvas.toDataURL('image/png');  // Base64 string
# Backend converts:
def save_base64_image(base64_string, folder):
    base64_string = base64_string.split(',')[1]  # Remove 'data:image/png;base64,'
    image_data = base64.b64decode(base64_string)
    return ContentFile(image_data, name=f"{timezone.now().strftime('%Y%m%d_%H%M%S')}.png")
```

### 3. Sell Agreement Creation
```python
# agreements/views.py::create_agreement() - Line 373 forces type to 'sell'
agreement = form.save(commit=False)
agreement.agreement_type = 'sell'  # HARDCODED
agreement.seller = request.user

# Ownership validation:
if phone.current_owner != request.user:
    messages.error(request, 'You can only sell your own phones.')
    return redirect('phone_list')

if phone.status != 'available':
    messages.error(request, 'Phone must be available to sell.')
    return redirect('phone_detail', phone_id=phone.id)

# On success:
phone.status = 'sold'
phone.save()
PhoneHistory.objects.create(phone=phone, action='sell', from_user=request.user, agreement=agreement)
```

### 4. Phone Assignment Workflow
```python
# agreements/views.py::assign_phone()
PhoneAssignment.objects.create(
    phone=phone, from_seller=request.user, to_seller=recipient, status='pending'
)
phone.status = 'assigned'
PhoneHistory.objects.create(action='assign', from_user=request.user, to_user=recipient)

# agreements/views.py::handle_assignment()
if action == 'approve':
    phone.current_owner = assignment.to_seller
    phone.status = 'available'
    assignment.status = 'approved'
elif action == 'reject':
    phone.status = 'available'  # Reverts to original owner
    assignment.status = 'rejected'
```

### 5. Manager Global Search
```python
# agreements/views.py::search_phone() - Managers only
if not request.user.is_manager():
    messages.error(request, 'Only managers can search phones globally.')
    return redirect('dashboard')

# Search across ALL sellers
phones = Phone.objects.filter(
    Q(imei__icontains=query) | Q(serial_number__icontains=query)
)
# Returns phones regardless of current_owner
```

### 6. PDF Generation Pattern
```python
# agreements/views.py::generate_agreement_pdf()
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Image handling:
id_photo_path = agreement.id_photo.path  # File system path
c.drawImage(id_photo_path, x, y, width, height)

# Signature from ImageField (NOT base64 text):
signature_img = ImageReader(agreement.signature_photo.path)
c.drawImage(signature_img, x, y, width, height)
```

## URL Routing & Access Control

### Key Endpoints
| Path | View | App | Access | Description |
|------|------|-----|--------|-------------|
| `/` | `dashboard` | accounts/agreements | All | Role-based redirect (seller/manager dashboards) |
| `/register/` | `register` | accounts | Public | Auto-suspends sellers on registration |
| `/login/` | `LoginView` | accounts | Public | Django auth |
| `/logout/` | `logout_to_login` | accounts | All | Logout and redirect |
| `/hold/` | `account_hold_notice` | accounts | Suspended | Suspension notice page |
| `/sellers/<id>/manage/` | `manage_seller_status` | accounts | Manager | Suspend/activate sellers |
| `/phones/` | `phone_list` | agreements | All | Filtered by `current_owner` for sellers |
| `/phones/add/` | `add_phone` | agreements | Seller | Creates phone + buy agreement |
| `/agreements/create/` | `create_agreement` | agreements | Seller | Sell agreement (webcam + signature) |
| `/agreements/pdf/<id>/<type>/` | `generate_agreement_pdf` | agreements | All | Download PDF (buy/sell) |
| `/assign/` | `assign_phone` | agreements | Seller | Assign phone to another seller |
| `/assignments/` | `assignment_requests` | agreements | Seller | View pending assignments |
| `/assignments/<id>/<action>/` | `handle_assignment` | agreements | Seller | Approve/reject assignment |
| `/search/` | `search_phone` | agreements | Manager | Global IMEI/serial search |
| `/reports/phone/<id>/` | `generate_phone_report` | agreements | Manager | Phone history PDF |
| `/admin/` | Django Admin | - | Manager | Staff access only |
### Role-Based Filtering Pattern
```python
# agreements/views.py::phone_list() - Import CustomUser from accounts
from accounts.models import CustomUser
from django.contrib.auth.decorators import login_required

@login_required
def phone_list(request):
    if request.user.is_seller():
        phones = Phone.objects.filter(current_owner=request.user)
    elif request.user.is_manager():
        phones = Phone.objects.all()  # No filter for managers
```     phones = Phone.objects.all()  # No filter for managers
```

### Validation Patterns
```python
# Phone number validation (Rwanda format)
customer_phone = models.CharField(max_length=15)
# Frontend regex: ^07[0-9]{8}$ (10 digits starting with 07)

# IMEI validation
imei = models.CharField(max_length=15, unique=True)
# Must be exactly 15 characters

# Permission checks in views
if not request.user.is_manager():
    messages.error(request, 'Manager access required.')
    return redirect('dashboard')
```

## Core Models & Database Schema

### CustomUser (extends AbstractUser) - `accounts/models.py`
```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    role = models.CharField(max_length=10, choices=[('seller', 'Seller'), ('manager', 'Manager')])
    phone_number = models.CharField(max_length=15)  # Format: 07XXXXXXXX
    address = models.TextField()
    signature = models.ImageField()  # Profile signature for agreements
    national_id = models.CharField(max_length=30)
    
    # SUSPENSION SYSTEM
    is_suspended = models.BooleanField(default=False)
    suspended_at = models.DateTimeField(null=True)
    suspended_reason = models.TextField(blank=True)
    suspended_by = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    
    def is_seller(self): return self.role == 'seller'
    def is_manager(self): return self.role == 'manager'
```

**Critical**: New sellers auto-suspended with `suspended_reason="Awaiting manager activation"` on registration.

### Phone (Inventory Management) - `agreements/models.py`
```python
# agreements/models.py
from django.db import models
from accounts.models import CustomUser  # Import from accounts app

class Phone(models.Model):
    imei = models.CharField(max_length=15, unique=True)  # 15-digit unique identifier
    serial_number = models.CharField(max_length=50, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    condition = models.CharField(choices=[('new', 'New'), ('used', 'Used'), ('other', 'Other')])
    
    # STATUS LIFECYCLE: available → sold (via sell agreement)
    #                   available → assigned (via assignment)
    #                   assigned → available (assignment resolved)
    status = models.CharField(choices=[('available', 'Available'), ('sold', 'Sold'), ('assigned', 'Assigned')])
    
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    current_owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # FK to accounts.CustomUser
    created_at = models.DateTimeField(auto_now_add=True)
```

**Business Rules**:
- Only `status='available'` phones can be sold or assigned
- Only `current_owner` can sell or assign a phone
- IMEI/serial must be unique across entire system

### Agreement (Legal Documentation) - `agreements/models.py`
```python
class Agreement(models.Model):
    agreement_type = models.CharField(choices=[('buy', 'Buy Agreement'), ('sell', 'Sell Agreement')])
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # FK to accounts.CustomUser
    
    # Customer/Previous Owner Info
    customer_name = models.CharField(max_length=100)
    customer_national_id = models.CharField(max_length=30)
    customer_phone = models.CharField(max_length=15)  # Validates: ^07[0-9]{8}$
    customer_address = models.TextField()
    
    # DUAL STORAGE for document capture
    id_photo = models.ImageField(upload_to='agreements/id_photos/')
    passport_photo = models.ImageField(upload_to='agreements/passport_photos/')
    signature = models.TextField()  # Base64 canvas data for HTML rendering
    signature_photo = models.ImageField(upload_to='agreements/signatures/')  # Image file for PDF
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Document Capture Pattern**:
1. Webcam captures → `canvas.toDataURL('image/png')` → base64 string
2. Frontend sends base64 in POST request
3. Backend: `save_base64_image()` converts to `ContentFile`, saves to ImageField
4. Signature stored TWICE: base64 text (for canvas replay) + image file (for PDF)

## Common Tasks & Solutions

### Creating a New View
```python
# 1. For auth-related views: accounts/views.py
# 2. For phone/agreement views: agreements/views.py

# Example in agreements/views.py:
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.models import CustomUser  # Import from accounts

@login_required
def my_view(request):
    if not request.user.is_seller():
        messages.error(request, 'Seller access required.')
        return redirect('dashboard')
    
    # Business logic here
    context = {'data': data}
    return render(request, 'agreements/my_template.html', context)

# 2. Add URL route in PAM/urls.py
path('my-route/', views.my_view, name='my_view'),

# 3. Create template in appropriate app:
#    accounts/templates/accounts/ OR agreements/templates/agreements/
``` created_at = models.DateTimeField(auto_now_add=True)
```

**Assignment Workflow**:
1. Seller A assigns phone → `phone.status='assigned'`, creates `PhoneAssignment(status='pending')`
2. Seller B approves → `phone.current_owner=Seller B`, `phone.status='available'`
3. Seller B rejects → `phone.status='available'`, owner unchanged

### Sales Models - `sales/models.py`

**SalesTransaction** - Individual sale records:
```python
# sales/models.py
from accounts.models import CustomUser
from agreements.models import Phone, Agreement

class SalesTransaction(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True)
    seller = models.ForeignKey(CustomUser, limit_choices_to={'role': 'seller'})
    phone = models.ForeignKey(Phone, on_delete=models.PROTECT)
    agreement = models.OneToOneField(Agreement, null=True)
    
    # Financial details
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2)  # Auto-calculated
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Auto-calculated
    
    # Payment & status
    payment_method = models.CharField(choices=[('cash', 'Cash'), ('mobile_money', 'Mobile Money'), ...])
    status = models.CharField(choices=[('completed', 'Completed'), ('pending', 'Pending'), ...])
```

**SellerPerformance** - Performance metrics aggregation:
- Tracks daily/weekly/monthly/quarterly/yearly performance
- Metrics: total_sales, total_revenue, total_profit, average_profit_margin
- Calculated via `calculate_performance()` classmethod

**SalesTarget** - Goals and targets:
- Target types: sales_count, revenue, profit
- Tracks achievement percentage
- Built-in `update_progress()` and `check_achievement()` methods

**Customer** - Customer relationship management:
- Tracks repeat customers
- Metrics: total_purchases, total_spent, average_purchase_value
- Auto-updates via `update_metrics()` method

**Key Features**:
- Auto-calculates profit (sale_price - cost_price) and commission on save
- Generates unique transaction IDs automatically
- Performance records can be bulk-generated for reporting
- Targets update progress automatically from SalesTransaction data

## Common Tasks & Solutions

### Creating a New View
```python
# 1. Define in agreements/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

@login_required
def my_view(request):
    if not request.user.is_seller():
        messages.error(request, 'Seller access required.')
        return redirect('dashboard')
    
    # Business logic here
    context = {'data': data}
    return render(request, 'agreements/my_template.html', context)

# 2. Add URL route in PAM/urls.py
path('my-route/', views.my_view, name='my_view'),

# 3. Create template in agreements/templates/agreements/my_template.html
```

### Searching & Filtering
```python
# IMEI/Serial search (case-insensitive, partial match)
from django.db.models import Q
phones = Phone.objects.filter(
    Q(imei__icontains=query) | Q(serial_number__icontains=query)
)

# Filter with related user data
phones = Phone.objects.filter(status='available').select_related('current_owner')
# Reduces queries by joining User table
### Debug & Troubleshooting
```python
# Enable SQL query logging in view
from django.db import connection
print(connection.queries)  # See all queries executed

# Shell commands for testing
python manage.py shell
>>> from accounts.models import CustomUser
>>> from agreements.models import Phone, Agreement
>>> Phone.objects.filter(status='available').count()
>>> CustomUser.objects.filter(is_suspended=True)
```
# Save base64 image
if request.POST.get('id_photo_base64'):
    agreement.id_photo = save_base64_image(
        request.POST['id_photo_base64'], 
        'agreements/id_photos'
    )

# Access in template
<img src="{{ agreement.id_photo.url }}" alt="ID Photo">

# Check file exists
if agreement.id_photo and os.path.exists(agreement.id_photo.path):
    # Use agreement.id_photo.path for ReportLab
```

### Debug & Troubleshooting
```python
# Enable SQL query logging in view
from django.db import connection
print(connection.queries)  # See all queries executed

# Shell commands for testing
python manage.py shell
>>> from agreements.models import *
>>> Phone.objects.filter(status='available').count()
>>> CustomUser.objects.filter(is_suspended=True)
```

## Important Notes & Gotchas

### Critical Business Rules
1. **Phone Status Lifecycle**: `available` → `sold` (irreversible) OR `available` → `assigned` → `available`
2. **Ownership Validation**: ALWAYS check `phone.current_owner == request.user` before modifications
### Security & Permissions
- **Seller Isolation**: Sellers see ONLY `current_owner=request.user` phones
- **Manager Override**: Managers bypass all ownership filters via `Phone.objects.all()`
- **Middleware Order**: `SuspensionMiddleware` in accounts app MUST be after `AuthenticationMiddleware`
- **CSRF Protection**: All forms require `{% csrf_token %}`
- **File Validation**: Only ImageField validates uploaded files are images
- **Cross-App Import**: Always import `CustomUser` from `accounts.models` in agreements app
### Security & Permissions
- **Seller Isolation**: Sellers see ONLY `current_owner=request.user` phones
- **Manager Override**: Managers bypass all ownership filters via `Phone.objects.all()`
- **Middleware Order**: `SuspensionMiddleware` MUST be after `AuthenticationMiddleware`
- **CSRF Protection**: All forms require `{% csrf_token %}`
- **File Validation**: Only ImageField validates uploaded files are images

### Common Pitfalls
```python
# ❌ WRONG: Allows selling others' phones
phone = Phone.objects.get(id=phone_id)
phone.status = 'sold'

# ✅ CORRECT: Validate ownership first
phone = get_object_or_404(Phone, id=phone_id, current_owner=request.user)
if phone.status != 'available':
    return redirect('phone_list')
phone.status = 'sold'

# ❌ WRONG: Hard deletes lose audit trail
agreement.delete()

# ✅ CORRECT: Mark as inactive/void (if implementing soft delete)
agreement.is_voided = True
agreement.voided_at = timezone.now()
```

### Media Files Configuration
- **Development**: Django serves media files via `urlpatterns += static(settings.MEDIA_URL, ...)`
- **Production**: Use nginx/Apache to serve `MEDIA_ROOT` directory
- **HTTPS Required**: Webcam access requires HTTPS in production (security policy)

### Testing & Data Management
```cmd
:: Create test users and phones
python manage.py create_sample_data --sellers 5 --phones 20

:: Reset database (DELETES ALL DATA)
del db.sqlite3
python manage.py migrate

:: Create manager account
python manage.py createsuperuser
:: Choose: role=manager, is_staff=True

:: Access admin panel
http://localhost:8000/admin/
```
def seller_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.profile.role != 'SELLER':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
```

### IMEI Lookup (Critical Feature)
Implement efficient IMEI search for authority verification:
```python
# agreements/views.py
def verify_phone(request, imei):
    agreements = Agreement.objects.filter(
        phone_imei=imei, 
        is_deleted=False
    ).select_related('seller').order_by('-created_at')
    # Returns full chain of custody
```

## Important Notes

- **Admin Interface**: Available at `/admin/` after running migrations and creating superuser
## Testing & Debugging

### Running Tests
### Shell Testing Patterns
```python
# python manage.py shell
from accounts.models import CustomUser
from agreements.models import Phone, Agreement, PhoneHistory, PhoneAssignment
from django.contrib.auth import get_user_model

# Create test seller
User = get_user_model()
seller = User.objects.create_user(
    username='testseller', 
    password='testpass',
    role='seller',
    phone_number='0781234567'
)

# Test phone creation
phone = Phone.objects.create(
    imei='123456789012345',
    serial_number='SN12345',
    brand='Samsung',
    model='Galaxy S21',
    status='available',
    current_owner=seller
)

# Test assignment workflow
from django.utils import timezone
assignment = PhoneAssignment.objects.create(
    phone=phone,
    from_seller=seller1,
    to_seller=seller2,
    status='pending'
)
```m django.utils import timezone
assignment = PhoneAssignment.objects.create(
    phone=phone,
    from_seller=seller1,
    to_seller=seller2,
    status='pending'
)
```

### Debug Techniques
```python
# View debug info in template
{% if debug %}
  <pre>{{ object|pprint }}</pre>
{% endif %}

# Print in view (shows in console)
print(f"Phone status: {phone.status}, Owner: {phone.current_owner}")

# Django Debug Toolbar (install via pip)
INSTALLED_APPS += ['debug_toolbar']
### Common Error Solutions
**Error**: `AUTH_USER_MODEL is not defined`  
**Fix**: Ensure `AUTH_USER_MODEL = 'accounts.CustomUser'` in settings BEFORE migrations, and `accounts` app is in INSTALLED_APPS

**Error**: `No module named 'accounts'`  
**Fix**: Ensure `accounts` app is created and listed in INSTALLED_APPS before `agreements`

**Error**: `Cannot import name 'CustomUser' from 'agreements.models'`  
**Fix**: CustomUser is in `accounts.models`, not `agreements.models`. Update import: `from accounts.models import CustomUser`
### Common Error Solutions
**Error**: `AUTH_USER_MODEL is not defined`  
**Fix**: Ensure `AUTH_USER_MODEL = 'agreements.CustomUser'` in settings BEFORE migrations

**Error**: `Webcam not accessible`  
**Fix**: HTTPS required in production, check browser permissions, verify `getUserMedia()` support

**Error**: `Image not found for PDF`  
**Fix**: Check `agreement.id_photo.path` exists, verify MEDIA_ROOT configured, ensure file saved properly

**Error**: `Seller can access other sellers' phones`  
**Fix**: Always filter by `current_owner=request.user` in seller views

**Error**: `Assignment stuck in pending`  
**Fix**: Check `phone.status='assigned'`, verify recipient can see assignment at `/assignments/`

## Production Deployment Checklist

```python
# settings.py changes for production
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')  # Use environment variable
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        # ... other PostgreSQL config
    }
}

# Serve media files via nginx/Apache, not Django
# Configure S3/cloud storage for MEDIA_ROOT
```

**Deployment Steps**:
1. ✅ Change SECRET_KEY to random secure value
2. ✅ Set DEBUG=False
3. ✅ Configure ALLOWED_HOSTS
## Quick Reference

### App Responsibilities
**accounts app**:
- CustomUser model (authentication, roles, suspension)
- Registration, login, logout views
- SuspensionMiddleware
- Seller activation/suspension management
- Auth-related templates (login.html, register.html, hold.html)

**agreements app**:
- Phone, Agreement, PhoneHistory, PhoneAssignment models
- Phone operations (add, list, detail, assign)
- Agreement creation, PDF generation
- Phone history and reporting
- Dashboard views
- Agreement-related templates

### Model Relationships
```
accounts.CustomUser (role: seller/manager, is_suspended)
    └── agreements.Phone (current_owner FK to CustomUser)
            ├── agreements.Agreement (phone FK, seller FK to CustomUser)
            ├── agreements.PhoneHistory (phone FK, from_user/to_user FK to CustomUser)
            └── agreements.PhoneAssignment (phone FK, from/to sellers FK to CustomUser)
```
### Model Relationships
```
CustomUser (role: seller/manager, is_suspended)
    └── Phone (current_owner FK)
            ├── Agreement (phone FK, seller FK)
            ├── PhoneHistory (phone FK, immutable audit)
            └── PhoneAssignment (phone FK, from/to sellers)
```

### Status Transitions
```
Phone.status:
  'available' --[create sell agreement]--> 'sold' (final)
  'available' --[assign to seller]--> 'assigned'
  'assigned' --[approve/reject]--> 'available'

PhoneAssignment.status:
  'pending' --[approve]--> 'approved' (ownership transfers)
  'pending' --[reject]--> 'rejected' (ownership unchanged)

CustomUser.is_suspended:
  True --> Redirect to /hold/ (except /logout/)
  False --> Normal access
```

### File Paths
```
media/
  └── agreements/
        ├── id_photos/          # Customer ID photos
        ├── passport_photos/    # Customer passport photos
        └── signatures/         # Digital signatures as images
```

---

**System Version**: 1.0  
**Django Version**: 5.2.4  
**Python**: 3.8+  
**Last Updated**: December 8, 2025
## Testing & Debugging
- Run tests: `python manage.py test <app>`
- Check for issues: `python manage.py check`
- Show migrations: `python manage.py showmigrations`
- SQL inspection: `python manage.py sqlmigrate <app> <migration_number>`
