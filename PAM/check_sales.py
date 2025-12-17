import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PAM.settings')
django.setup()

from sales.models import SalesTransaction
from accounts.models import CustomUser

print("=" * 60)
print("SALES TRANSACTION CHECK")
print("=" * 60)

total = SalesTransaction.objects.count()
print(f"\nTotal Sales Transactions: {total}")

if total > 0:
    print("\nSample Transactions:")
    for t in SalesTransaction.objects.all()[:10]:
        print(f"  ID: {t.id}")
        print(f"  Transaction ID: {t.transaction_id}")
        print(f"  Seller: {t.seller.username} ({t.seller.role})")
        print(f"  Phone: {t.phone.brand} {t.phone.model}")
        print(f"  Customer: {t.customer_name}")
        print(f"  Sale Price: RWF {t.sale_price}")
        print(f"  Cost Price: RWF {t.cost_price}")
        print(f"  Profit: RWF {t.profit}")
        print(f"  Date: {t.sale_date}")
        print(f"  Status: {t.status}")
        print("-" * 60)
else:
    print("\n⚠️ No sales transactions found in database!")
    print("Please create a sale transaction by:")
    print("1. Going to Phones list")
    print("2. Click 'Sell' on an available phone")
    print("3. Fill in customer details and complete the sale")

print("\n" + "=" * 60)
print("USER CHECK")
print("=" * 60)

sellers = CustomUser.objects.filter(role='seller')
managers = CustomUser.objects.filter(role='manager')

print(f"\nSellers: {sellers.count()}")
for seller in sellers:
    seller_sales = SalesTransaction.objects.filter(seller=seller).count()
    print(f"  - {seller.username}: {seller_sales} sales")

print(f"\nManagers: {managers.count()}")
for manager in managers:
    print(f"  - {manager.username}")

print("\n" + "=" * 60)
