from django import forms
from datetime import date as today_date
from .models import Appointment, AvailabilitySlot

NATTES_CHOICES = [
    ('', '— Sélectionnez —'),
    ('oui', 'Oui, j\'ai déjà mes nattes (prix normal)'),
    ('non', 'Non, je n\'ai pas encore mes nattes (+10 $ CAD)'),
]


class AppointmentForm(forms.ModelForm):
    slot = forms.ModelChoiceField(
        queryset=AvailabilitySlot.objects.none(),
        label='Créneau disponible',
        empty_label='— Choisir un créneau —',
    )
    nattes_deja_faites = forms.ChoiceField(
        choices=NATTES_CHOICES,
        required=False,
        label='Avez-vous déjà vos nattes ?',
    )

    class Meta:
        model = Appointment
        fields = ['customer_name', 'customer_email', 'service', 'slot']
        labels = {
            'customer_name': 'Votre nom',
            'customer_email': 'Votre email',
            'service': 'Service',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer_email'].required = True
        self.fields['slot'].queryset = AvailabilitySlot.objects.filter(
            is_booked=False,
            date__gte=today_date.today()
        ).order_by('date', 'time')
