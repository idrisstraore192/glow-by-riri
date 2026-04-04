import calendar
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Count, F


def home(request):
    return render(request, "core/home.html")


# ── Feature 5: Admin Dashboard ────────────────────────────────────────────────
@staff_member_required
def admin_dashboard(request):
    from shop.models import Order, OrderItem, Product
    from booking.models import Appointment

    now = timezone.now()
    today = timezone.localdate()
    # Current month boundaries
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Next month start (for range)
    if now.month == 12:
        month_end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        month_end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Week boundaries
    week_start = today - timezone.timedelta(days=today.weekday())
    week_end = week_start + timezone.timedelta(days=7)

    # Revenue this month
    revenue_month = Order.objects.filter(
        paid=True, created_at__gte=month_start, created_at__lt=month_end
    ).aggregate(total=Sum('total'))['total'] or 0

    # Orders this month
    orders_month = Order.objects.filter(
        paid=True, created_at__gte=month_start, created_at__lt=month_end
    ).count()

    # Appointments this month
    appts_month = Appointment.objects.filter(
        date__gte=month_start.date(), date__lt=month_end.date()
    ).count()

    # Unshipped recent orders
    unshipped_orders = Order.objects.filter(paid=True, shipped=False).order_by('-created_at')[:10]

    # Upcoming appointments this week
    upcoming_appts = Appointment.objects.filter(
        date__gte=today, date__lt=week_end
    ).select_related('service').order_by('date', 'time')[:10]

    # Top 5 products sold
    top_products = (
        OrderItem.objects.values('product_name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )

    context = {
        'revenue_month': revenue_month,
        'orders_month': orders_month,
        'appts_month': appts_month,
        'unshipped_orders': unshipped_orders,
        'upcoming_appts': upcoming_appts,
        'top_products': top_products,
        'title': 'Tableau de bord',
    }
    return render(request, 'admin/dashboard.html', context)


# ── Feature 2: Booking Calendar ───────────────────────────────────────────────
@staff_member_required
def booking_calendar(request):
    from booking.models import Appointment

    today = timezone.localdate()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Navigation
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    # Appointments for this month
    appts = Appointment.objects.filter(
        date__year=year, date__month=month
    ).select_related('service').order_by('date', 'time')

    # Group by day
    appts_by_day = {}
    for appt in appts:
        day = appt.date.day
        if day not in appts_by_day:
            appts_by_day[day] = []
        appts_by_day[day].append(appt)

    # Build calendar weeks
    cal = calendar.monthcalendar(year, month)
    month_name = [
        '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ][month]

    weeks = []
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({'day': None, 'appts': []})
            else:
                week_days.append({'day': day, 'appts': appts_by_day.get(day, [])})
        weeks.append(week_days)

    context = {
        'weeks': weeks,
        'month_name': month_name,
        'year': year,
        'month': month,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'title': f'Calendrier — {month_name} {year}',
    }
    return render(request, 'admin/booking_calendar.html', context)
