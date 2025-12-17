# Phone Agreement Management (PAM) System

A comprehensive Django-based web application for managing phone sales, purchases, agreements, and inventory tracking with role-based access control.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [User Roles](#user-roles)
- [Main Modules](#main-modules)
- [Database Models](#database-models)
- [Usage Guide](#usage-guide)
- [API Routes](#api-routes)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The Phone Agreement Management (PAM) System is a complete business management solution designed for phone retailers and sellers. It streamlines the entire process of phone inventory management, sales tracking, purchase agreements, and inter-seller phone assignments with automated profit calculation and comprehensive reporting.

## ✨ Features

### Core Features
- **User Management**
  - Role-based access control (Manager, Seller, Superuser)
  - Seller self-registration with manager approval workflow
  - Account suspension/activation system
  - Digital signature management for agreements

- **Inventory Management**
  - Complete phone inventory tracking (Available, Sold, Assigned)
  - Phone details: Brand, Model, IMEI, Specifications, Purchase Price
  - Automatic profit calculation (Sell Price - Purchase Price)
  - Phone status lifecycle management

- **Agreement System**
  - Buy agreements (purchase from suppliers)
  - Sell agreements (sales to customers)
  - PDF generation with digital signatures
  - Unique agreement numbering (AGR-XXXXXX)
  - Customer information tracking

- **Phone Assignment**
  - Transfer phones between sellers
  - Approval workflow (Pending → Approved/Rejected)
  - Assignment tracking with unique IDs (ASSIGN-XXXXXX)

- **Phones History**
  - Unified view of all phone activities (Buy, Sell, Assign)
  - Advanced filtering (activity type, seller, date range)
  - Pagination support
  - CSV report generation

- **Sales Dashboard** (Sellers Only)
  - Personal sales statistics
  - Revenue and profit tracking
  - Period-based filtering (Daily, Weekly, Monthly, Quarterly, Yearly)
  - Interactive charts (Chart.js)
  - Recent transactions view

- **Manager Dashboard**
  - System-wide statistics
  - Pending seller approvals
  - Recent agreements overview
  - Phones history preview
  - Top performers ranking
  - Inventory overview

- **Reporting**
  - CSV export for phones history
  - Customizable date ranges
  - Activity-specific reports

## 🛠 Technology Stack

### Backend
- **Django 5.2.4** - Web framework
- **Python 3.11+** - Programming language
- **SQLite** - Database (development)

### Frontend
- **Bootstrap 5.3.0** - UI framework
- **Font Awesome 6.4.0** - Icons
- **Chart.js 4.4.0** - Data visualization
- **JavaScript (ES6+)** - Client-side scripting

### Key Libraries
- **ReportLab** - PDF generation
- **Pillow** - Image processing
- **Django Forms** - Form handling
- **Django Messages** - User notifications

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/MugaboVedaste/Phone-Agreement-Management.git
cd Phone-Agreement-Management/PAM
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Apply database migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Run development server**
```bash
python manage.py runserver
```

7. **Access the application**
- Open browser: `http://127.0.0.1:8000/`
- Admin panel: `http://127.0.0.1:8000/admin/`

## 📁 Project Structure

```
Phone-Agreement-Management/
├── PAM/
│   ├── manage.py
│   ├── db.sqlite3
│   ├── requirements.txt
│   │
│   ├── PAM/                      # Project configuration
│   │   ├── __init__.py
│   │   ├── settings.py           # Django settings
│   │   ├── urls.py               # Main URL routing
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── accounts/                 # User management app
│   │   ├── models.py            # CustomUser model
│   │   ├── views.py             # Authentication & user views
│   │   ├── forms.py             # User forms
│   │   ├── middleware.py        # Suspension middleware
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── agreements/               # Agreements & inventory app
│   │   ├── models.py            # Phone, Agreement, PhoneAssignment
│   │   ├── views.py             # CRUD operations
│   │   ├── forms.py             # Agreement forms
│   │   ├── utils.py             # PDF generation utilities
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── sales/                    # Sales tracking app
│   │   ├── models.py            # SalesTransaction, Performance, Targets
│   │   ├── views.py             # Dashboard & analytics
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── templates/                # HTML templates
│   │   ├── base.html            # Base template with navigation
│   │   ├── accounts/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   ├── manager_dashboard.html
│   │   │   ├── phone_history.html
│   │   │   └── ...
│   │   ├── agreements/
│   │   │   ├── phone_list.html
│   │   │   ├── agreement_form.html
│   │   │   ├── agreement_detail.html
│   │   │   └── ...
│   │   └── sales/
│   │       ├── dashboard.html
│   │       └── ...
│   │
│   ├── static/                   # Static files
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   └── media/                    # User uploads
│       └── signatures/           # Digital signatures
```

## 👥 User Roles

### 1. Superuser
- Full system access
- Can create manager accounts
- Database administration via Django admin

### 2. Manager
- Approve/reject seller registrations
- View all system activities
- Access phones history with filters
- Generate system-wide reports
- Manage seller accounts (suspend/activate)
- View inventory and agreements
- Cannot perform sales transactions

### 3. Seller
- Self-registration (requires manager approval)
- Create buy/sell agreements
- View personal phones inventory
- Assign phones to other sellers
- Access personal sales dashboard
- Generate personal sales reports
- Cannot access other sellers' data

## 🔧 Main Modules

### 1. Accounts Module
**Purpose**: User authentication and authorization

**Key Components**:
- CustomUser model with role-based permissions
- Registration with automatic suspension
- Login/logout functionality
- Profile management with digital signatures
- Manager approval workflow
- Suspension middleware

**Files**:
- `accounts/models.py` - CustomUser model
- `accounts/views.py` - Auth views
- `accounts/middleware.py` - SuspensionMiddleware

### 2. Agreements Module
**Purpose**: Phone inventory and agreements management

**Key Components**:
- Phone model with status tracking
- Agreement model (buy/sell types)
- PhoneAssignment model for transfers
- PDF generation with signatures
- CRUD operations for phones and agreements

**Files**:
- `agreements/models.py` - Phone, Agreement, PhoneAssignment
- `agreements/views.py` - CRUD views
- `agreements/utils.py` - PDF utilities

### 3. Sales Module
**Purpose**: Sales tracking and analytics

**Key Components**:
- Sales transaction tracking
- Seller performance metrics
- Sales targets management
- Dashboard with charts
- Period-based filtering

**Files**:
- `sales/models.py` - SalesTransaction, SellerPerformance
- `sales/views.py` - Dashboard and analytics

## 🗄 Database Models

### CustomUser
```python
- username, email, password
- first_name, last_name, phone_number
- role: 'manager' | 'seller'
- is_suspended: boolean
- suspended_reason, suspended_at, suspended_by
- signature: ImageField
- address, national_id
```

### Phone
```python
- brand, model, imei (unique)
- storage, ram, color, condition
- purchase_price, purchase_date
- status: 'available' | 'sold' | 'assigned'
- seller: FK(CustomUser)
- created_at, updated_at

Methods:
- get_profit(): Calculate sell price - purchase price
- get_purchase_agreement(): Get buy agreement
- get_sell_agreement(): Get sell agreement
```

### Agreement
```python
- agreement_number: Unique (AGR-XXXXXX)
- agreement_type: 'buy' | 'sell'
- phone: FK(Phone)
- seller: FK(CustomUser)
- customer_name, customer_phone, customer_email
- price, payment_method, payment_status
- terms_conditions, notes
- created_at, updated_at

Properties:
- buyer_name: Returns customer_name
- agreed_price: Returns price
```

### PhoneAssignment
```python
- from_seller: FK(CustomUser)
- to_seller: FK(CustomUser)
- phone: FK(Phone)
- reason: TextField
- status: 'pending' | 'approved' | 'rejected'
- reviewed_by: FK(CustomUser, nullable)
- reviewed_at: DateTime
- created_at, updated_at
```

### SalesTransaction
```python
- transaction_id: Unique
- phone: FK(Phone)
- seller: FK(CustomUser)
- customer: FK(Customer)
- sale_price, profit
- sale_date
- payment_method, payment_status
- status: 'completed' | 'pending' | 'cancelled'
```

## 📖 Usage Guide

### For Sellers

#### 1. Registration
1. Navigate to registration page
2. Fill in personal details
3. Submit form
4. Wait for manager approval
5. Login after approval

#### 2. Creating a Buy Agreement
1. Go to "Agreements" → "New Agreement"
2. Select "Buy" as agreement type
3. Enter phone details (IMEI, brand, model, etc.)
4. Enter supplier information
5. Set purchase price
6. Submit to create phone in inventory

#### 3. Creating a Sell Agreement
1. Go to "Phones" → Select available phone
2. Click "Create Agreement"
3. Select "Sell" as agreement type
4. Enter customer information
5. Set selling price
6. Submit to complete sale
7. Download PDF agreement

#### 4. Assigning Phone to Another Seller
1. Go to "Phones" → Select your phone
2. Click "Assign Phone"
3. Select receiving seller
4. Provide reason for assignment
5. Submit request
6. Wait for approval

#### 5. Viewing Sales Dashboard
1. Navigate to "Sales Dashboard"
2. Select period filter (Daily, Weekly, Monthly, etc.)
3. View statistics and charts
4. Click "Download My Sales" for CSV report

### For Managers

#### 1. Approving New Sellers
1. Go to "Manager Dashboard"
2. View "Pending Seller Approvals" section
3. Click "Review" on pending seller
4. Review seller details
5. Click "Approve" or "Reject"

#### 2. Managing Sellers
1. Navigate to "Manage Sellers"
2. View all sellers with status
3. Use "Suspend" to deactivate seller
4. Use "Activate" to reactivate seller
5. View seller details and activity

#### 3. Viewing Phones History
1. Go to "Phones History" (main navigation)
2. Use filters:
   - Activity Type (Buy/Sell/Assign)
   - Seller (dropdown)
   - Date Range (start/end dates)
3. Click "Filter" to apply
4. Click "Generate Report" for CSV export

#### 4. Reviewing Phone Assignments
1. Go to "Agreements" → "Assignments"
2. View pending assignments
3. Click on assignment to review
4. Approve or reject with reason

## 🌐 API Routes

### Authentication Routes
```
GET  /                          - Home page
GET  /register/                 - Seller registration
POST /register/                 - Submit registration
GET  /login/                    - Login page
POST /login/                    - Authenticate user
GET  /logout/                   - Logout user
GET  /hold/                     - Suspended account notice
```

### Manager Routes
```
GET  /manager/dashboard/                        - Manager dashboard
GET  /manager/phone-history/                    - Phones history with filters
GET  /manager/sellers/                          - Manage sellers
GET  /manager/sellers/pending/                  - Pending approvals
GET  /manager/sellers/<id>/approve/             - Approve/reject seller
POST /manager/sellers/<id>/approve/             - Submit approval decision
GET  /manager/sellers/<id>/toggle/              - Toggle seller status
```

### Phone & Inventory Routes
```
GET  /phones/                                    - List all phones
GET  /phones/create/                            - Create phone form
POST /phones/create/                            - Submit new phone
GET  /phones/<id>/                              - Phone details (removed)
GET  /phones/<id>/edit/                         - Edit phone (removed)
GET  /phones/<id>/assign/                       - Assign phone form
POST /phones/<id>/assign/                       - Submit assignment
```

### Agreement Routes
```
GET  /agreements/                               - List all agreements
GET  /agreements/create/                        - Create agreement form
POST /agreements/create/                        - Submit agreement
GET  /agreements/<id>/                          - Agreement details
GET  /agreements/<id>/pdf/                      - Download PDF
GET  /assignments/                              - List assignments
GET  /assignments/<id>/                         - Assignment details
POST /assignments/<id>/approve/                 - Approve assignment
POST /assignments/<id>/reject/                  - Reject assignment
```

### Sales Routes
```
GET  /sales/dashboard/                          - Sales dashboard (sellers only)
GET  /sales/transactions/                       - Transaction list
GET  /sales/report/                             - Generate report
```

## 🔐 Security Features

1. **Authentication Required**: All routes protected with `@login_required`
2. **Role-Based Access**: Permission checks for manager-only views
3. **CSRF Protection**: Django CSRF middleware enabled
4. **Password Hashing**: Django's built-in password hashing
5. **Suspension Middleware**: Automatic redirect for suspended users
6. **SQL Injection Protection**: Django ORM parameterized queries
7. **XSS Protection**: Django template auto-escaping

## 📊 Key Business Logic

### Profit Calculation
```python
# Automatically calculated for sold phones
profit = sell_agreement.price - phone.purchase_price
```

### Agreement Number Generation
```python
# Format: AGR-YYMMDD-XXXX (e.g., AGR-251217-0001)
agreement_number = f"AGR-{date.strftime('%y%m%d')}-{counter:04d}"
```

### Assignment Reference
```python
# Format: ASSIGN-XXXXXX (e.g., ASSIGN-000001)
reference = f"ASSIGN-{assignment.id:06d}"
```

### Phone Status Lifecycle
1. **Available** - Created via buy agreement
2. **Assigned** - Transferred to another seller (pending approval)
3. **Available** - Assignment approved, owned by new seller
4. **Sold** - Sold via sell agreement (final state)

## 🎨 UI Features

- **Responsive Design**: Mobile-friendly Bootstrap layout
- **Color-Coded Badges**: 
  - Buy: Blue (primary)
  - Sell: Green (success)
  - Assign: Yellow (warning)
- **Interactive Charts**: Real-time sales trend visualization
- **Modal Popups**: Phone details in modal (removed edit functionality)
- **Toast Notifications**: Success/error messages
- **Pagination**: 20 items per page

## 🧪 Testing

### Running Tests
```bash
python manage.py test accounts
python manage.py test agreements
python manage.py test sales
```

### Test Coverage Areas
- User registration and authentication
- Agreement creation and validation
- Phone assignment workflow
- Permission checks
- PDF generation
- Report generation

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Set up PostgreSQL database
4. Configure static files serving
5. Set up media files storage
6. Configure email backend
7. Use environment variables for secrets
8. Enable HTTPS
9. Configure CORS if needed
10. Set up logging

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:port/db
ALLOWED_HOSTS=yourdomain.com
```

## 📝 Recent Changes

### December 2024 Updates
- ✅ Removed phone editing functionality (phones are now immutable after creation)
- ✅ Added profit tracking and display in phone list
- ✅ Removed sales transaction tracking from dashboard
- ✅ Created unified Phones History view (buy, sell, assign)
- ✅ Added CSV report generation for phones history
- ✅ Created separate manager phones history page
- ✅ Updated navigation to separate seller and manager views
- ✅ Fixed Q import issue in sales views
- ✅ Implemented advanced filtering in phones history

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards
- Follow PEP 8 style guide
- Write docstrings for all functions
- Add comments for complex logic
- Write unit tests for new features
- Update documentation for API changes

## 📧 Support

For issues, questions, or contributions:
- **GitHub**: [MugaboVedaste/Phone-Agreement-Management](https://github.com/MugaboVedaste/Phone-Agreement-Management)
- **Email**: Contact repository owner

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Developer

**Mugabo Vedaste**
- GitHub: [@MugaboVedaste](https://github.com/MugaboVedaste)

## 🙏 Acknowledgments

- Django Software Foundation
- Bootstrap Team
- Chart.js Contributors
- Font Awesome Icons
- Stack Overflow Community

---

**Last Updated**: December 17, 2025  
**Version**: 1.0.0  
**Status**: Active Development
