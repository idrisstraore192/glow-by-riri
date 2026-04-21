import datetime
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.html import format_html
from .models import Service, ServiceImage, Appointment, AvailabilitySlot


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ['image_url', 'order']

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'deposit_amount', 'display_discount', 'duration']
    list_filter = ['category']
    fields = ['name', 'category', 'price', 'deposit_amount', 'discount_percent', 'duration', 'description', 'nattes_requises']
    inlines = [ServiceImageInline]

    def display_discount(self, obj):
        if obj.discount_percent and obj.discount_percent > 0:
            return f"-{obj.discount_percent:.0f}%"
        return "—"
    display_discount.short_description = "Rabais"

    class Media:
        js = ('https://upload-widget.cloudinary.com/latest/global/all.js', 'js/cloudinary_upload.js')


# ── Feature 1: Bulk slot generation ──────────────────────────────────────────
@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'date', 'time', 'is_booked']
    list_filter = ['is_booked', 'date']
    list_editable = ['is_booked']
    ordering = ['date', 'time']
    date_hierarchy = 'date'
    actions = ['generate_slots_action']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-slots/', self.admin_site.admin_view(self.generate_slots_view),
                 name='availabilityslot_generate_slots'),
        ]
        return custom_urls + urls

    def generate_slots_action(self, request, queryset):
        return redirect('admin:availabilityslot_generate_slots')
    generate_slots_action.short_description = "Générer des créneaux en lot"

    def generate_slots_view(self, request):
        context = dict(self.admin_site.each_context(request))
        DAYS = [
            ('0', 'Lundi'), ('1', 'Mardi'), ('2', 'Mercredi'),
            ('3', 'Jeudi'), ('4', 'Vendredi'), ('5', 'Samedi'), ('6', 'Dimanche'),
        ]
        errors = []
        success_msg = None

        if request.method == 'POST':
            try:
                date_start = datetime.date.fromisoformat(request.POST.get('date_start', ''))
                date_end = datetime.date.fromisoformat(request.POST.get('date_end', ''))
                time_start = datetime.time.fromisoformat(request.POST.get('time_start', ''))
                time_end = datetime.time.fromisoformat(request.POST.get('time_end', ''))
                duration = int(request.POST.get('duration', 60))
                selected_days = set(request.POST.getlist('days'))

                if date_end < date_start:
                    errors.append("La date de fin doit être après la date de début.")
                elif time_end <= time_start:
                    errors.append("L'heure de fin doit être après l'heure de début.")
                elif duration < 15:
                    errors.append("La durée minimale est de 15 minutes.")
                else:
                    created = 0
                    skipped = 0
                    current_date = date_start
                    delta = datetime.timedelta(days=1)
                    while current_date <= date_end:
                        if str(current_date.weekday()) in selected_days:
                            current_time = datetime.datetime.combine(current_date, time_start)
                            end_dt = datetime.datetime.combine(current_date, time_end)
                            while current_time < end_dt:
                                slot_time = current_time.time()
                                _, was_created = AvailabilitySlot.objects.get_or_create(
                                    date=current_date, time=slot_time
                                )
                                if was_created:
                                    created += 1
                                else:
                                    skipped += 1
                                current_time += datetime.timedelta(minutes=duration)
                        current_date += delta
                    success_msg = f"{created} créneau(x) créé(s), {skipped} ignoré(s) (doublon)."
            except (ValueError, TypeError) as e:
                errors.append(f"Données invalides : {e}")

        context.update({
            'title': 'Générer des créneaux en lot',
            'days': DAYS,
            'errors': errors,
            'success_msg': success_msg,
            'opts': AvailabilitySlot._meta,
        })
        return render(request, 'admin/generate_slots.html', context)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_email', 'service', 'date', 'time', 'deposit_paid', 'nattes_deja_faites', 'calendar_link']
    list_filter = ['deposit_paid', 'date', 'nattes_deja_faites']
    readonly_fields = ['stripe_session_id', 'deposit_paid', 'slot', 'nattes_deja_faites']
    ordering = ['-date', '-time']

    def calendar_link(self, obj):
        return format_html('<a href="/admin/booking/calendar/?year={}&month={}" target="_blank">Calendrier</a>',
                           obj.date.year, obj.date.month)
    calendar_link.short_description = "Calendrier"
