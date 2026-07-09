import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.shortcuts import render

from .models import Order, Product, OrderItem


@staff_member_required
def admin_dashboard(request):
    # Total revenue from completed orders
    completed_orders = Order.objects.filter(status=Order.STATUS_COMPLETED)
    total_revenue = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0

    # Order counts by status
    order_counts = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
    status_counts = {item['status']: item['count'] for item in order_counts}
    total_orders = Order.objects.count()

    # Top 5 best-selling products
    top_products = OrderItem.objects.values('product__name').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]

    # Low stock products
    low_stock_products = Product.objects.filter(stock__lt=5).order_by('stock')

    # Recent 10 orders
    recent_orders = Order.objects.order_by('-created_at')[:10]

    top_product_labels = [item["product__name"] or "Unknown" for item in top_products]
    top_product_values = [item["total_sold"] for item in top_products]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'status_counts': status_counts,
        'pending_count': status_counts.get(Order.STATUS_PENDING, 0),
        'processing_count': status_counts.get(Order.STATUS_PROCESSING, 0),
        'completed_count': status_counts.get(Order.STATUS_COMPLETED, 0),
        'top_product_labels': json.dumps(top_product_labels),
        'top_product_values': json.dumps(top_product_values),
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
    }
    return render(request, 'shop/admin_dashboard.html', context)
