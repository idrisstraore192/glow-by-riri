from django import forms
from datetime import date as today_date
from .models import Appointment, AvailabilitySlot, Service, ServiceRequest

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
        self.fields['service'].queryset = Service.objects.filter(sans_creneau=False)


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['customer_name', 'customer_email', 'service', 'message']
        labels = {
            'customer_name': 'Votre nom',
            'customer_email': 'Votre email',
            'service': 'Service demandé',
            'message': 'Message (optionnel)',
        }
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Décrivez votre demande, la perruque à customiser, la couleur souhaitée…',
            }),
        }

    def __init__(self, *args, **kwargs):
        initial_service_id = kwargs.pop('initial_service_id', None)
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(sans_creneau=True)
        self.fields['message'].required = False
        if initial_service_id:
            self.fields['service'].initial = initial_service_id
