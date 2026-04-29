"""
Tests automatiques — booking (services, formulaires, vues, modèles)
Lance avec : python manage.py test booking
"""
from decimal import Decimal
from datetime import date, time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from booking.models import Service, AvailabilitySlot, Appointment, ServiceRequest
from booking.forms import AppointmentForm, ServiceRequestForm


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_service(name="Pose perruque", price="80.00", discount=0,
                 nattes=False, sans_creneau=False, order=0, deposit=20.00):
    return Service.objects.create(
        name=name,
        price=Decimal(price),
        discount_percent=Decimal(str(discount)),
        nattes_requises=nattes,
        sans_creneau=sans_creneau,
        order=order,
        deposit_amount=Decimal(str(deposit)),
    )


def make_slot(days_ahead=3, slot_time=None, is_booked=False):
    d = date.today() + timedelta(days=days_ahead)
    t = slot_time or time(10, 0)
    return AvailabilitySlot.objects.create(date=d, time=t, is_booked=is_booked)


# ══════════════════════════════════════════════════════════════════════════════
# 1. MODÈLE SERVICE — final_price, ordering
# ══════════════════════════════════════════════════════════════════════════════

class ServiceModelTest(TestCase):

    def test_prix_sans_remise(self):
        s = make_service(price="80.00", discount=0)
        self.assertEqual(s.final_price, 80.0)

    def test_prix_avec_15_pourcent(self):
        s = make_service(price="100.00", discount=15)
        self.assertAlmostEqual(s.final_price, 85.0, places=2)

    def test_ordre_affichage_par_order_puis_price(self):
        s1 = make_service(name="Customisation", price="50.00", order=99)
        s2 = make_service(name="Pose Lace", price="120.00", order=0)
        services = list(Service.objects.all().order_by('order', 'price'))
        self.assertEqual(services[0].name, "Pose Lace")
        self.assertEqual(services[1].name, "Customisation")

    def test_sans_creneau_flag(self):
        s = make_service(sans_creneau=True)
        self.assertTrue(s.sans_creneau)


# ══════════════════════════════════════════════════════════════════════════════
# 2. MODÈLE APPOINTMENT — calcul prix, nattes
# ══════════════════════════════════════════════════════════════════════════════

class AppointmentModelTest(TestCase):

    def setUp(self):
        self.service = make_service(price="100.00", nattes=True)
        self.slot = make_slot()

    def _make_appt(self, nattes_deja_faites=None):
        return Appointment(
            customer_name="Cliente",
            customer_email="test@test.com",
            service=self.service,
            slot=self.slot,
            date=self.slot.date,
            time=self.slot.time,
            nattes_deja_faites=nattes_deja_faites,
        )

    def test_nattes_extra_si_pas_faites(self):
        appt = self._make_appt(nattes_deja_faites=False)
        self.assertEqual(appt.nattes_extra, 10.0)

    def test_nattes_extra_zero_si_deja_faites(self):
        appt = self._make_appt(nattes_deja_faites=True)
        self.assertEqual(appt.nattes_extra, 0.0)

    def test_nattes_extra_zero_si_non_applicable(self):
        appt = self._make_appt(nattes_deja_faites=None)
        self.assertEqual(appt.nattes_extra, 0.0)

    def test_total_price_avec_nattes(self):
        appt = self._make_appt(nattes_deja_faites=False)
        self.assertAlmostEqual(appt.total_price, 110.0, places=2)

    def test_total_price_sans_nattes(self):
        appt = self._make_appt(nattes_deja_faites=True)
        self.assertAlmostEqual(appt.total_price, 100.0, places=2)

    def test_total_price_avec_remise_service(self):
        service = make_service(price="100.00", discount=20, nattes=False)
        appt = Appointment(
            customer_name="C", customer_email="c@c.com",
            service=service, date=date.today(), time=time(10, 0),
        )
        # 100 * 0.80 = 80
        self.assertAlmostEqual(appt.total_price, 80.0, places=2)


# ══════════════════════════════════════════════════════════════════════════════
# 3. FORMULAIRE AppointmentForm — filtres services
# ══════════════════════════════════════════════════════════════════════════════

class AppointmentFormTest(TestCase):

    def test_services_sans_creneau_exclus(self):
        normal = make_service(name="Pose lace", sans_creneau=False)
        depot = make_service(name="Customisation", sans_creneau=True)
        form = AppointmentForm()
        qs = form.fields['service'].queryset
        self.assertIn(normal, qs)
        self.assertNotIn(depot, qs)

    def test_creneaux_passes_exclus(self):
        past_slot = AvailabilitySlot.objects.create(
            date=date.today() - timedelta(days=1), time=time(10, 0)
        )
        future_slot = make_slot(days_ahead=5)
        form = AppointmentForm()
        qs = form.fields['slot'].queryset
        self.assertNotIn(past_slot, qs)
        self.assertIn(future_slot, qs)

    def test_creneaux_deja_reserves_exclus(self):
        booked = make_slot(days_ahead=3, is_booked=True)
        free = make_slot(days_ahead=4)
        form = AppointmentForm()
        qs = form.fields['slot'].queryset
        self.assertNotIn(booked, qs)
        self.assertIn(free, qs)


# ══════════════════════════════════════════════════════════════════════════════
# 4. FORMULAIRE ServiceRequestForm — validation
# ══════════════════════════════════════════════════════════════════════════════

class ServiceRequestFormTest(TestCase):

    def setUp(self):
        self.service_depot = make_service(name="Coloration", sans_creneau=True)
        self.service_normal = make_service(name="Pose perruque", sans_creneau=False)

    def test_formulaire_valide(self):
        form = ServiceRequestForm(data={
            'customer_name': 'Marie',
            'customer_email': 'marie@test.com',
            'service': self.service_depot.id,
            'message': 'Perruque à teindre en brun',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_message_optionnel(self):
        form = ServiceRequestForm(data={
            'customer_name': 'Marie',
            'customer_email': 'marie@test.com',
            'service': self.service_depot.id,
            'message': '',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_invalide_rejete(self):
        form = ServiceRequestForm(data={
            'customer_name': 'Marie',
            'customer_email': 'pas-un-email',
            'service': self.service_depot.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('customer_email', form.errors)

    def test_service_normal_rejete_dans_formulaire_depot(self):
        form = ServiceRequestForm(data={
            'customer_name': 'Marie',
            'customer_email': 'marie@test.com',
            'service': self.service_normal.id,
        })
        self.assertFalse(form.is_valid())

    def test_nom_vide_rejete(self):
        form = ServiceRequestForm(data={
            'customer_name': '',
            'customer_email': 'marie@test.com',
            'service': self.service_depot.id,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('customer_name', form.errors)

    def test_initial_service_preselectionne(self):
        form = ServiceRequestForm(initial_service_id=self.service_depot.id)
        self.assertEqual(form.fields['service'].initial, self.service_depot.id)


# ══════════════════════════════════════════════════════════════════════════════
# 5. VUE service_request — GET et POST
# ══════════════════════════════════════════════════════════════════════════════

class ServiceRequestViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.service = make_service(name="Coloration", sans_creneau=True)
        self.url = reverse('service_request')

    def test_get_affiche_formulaire(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Faire une demande')

    def test_get_avec_service_id_preselectionne(self):
        resp = self.client.get(f"{self.url}?service={self.service.id}")
        self.assertEqual(resp.status_code, 200)

    def test_get_avec_service_id_invalide_pas_500(self):
        resp = self.client.get(f"{self.url}?service=abc")
        self.assertEqual(resp.status_code, 200)

    def test_get_avec_service_id_inexistant_pas_500(self):
        resp = self.client.get(f"{self.url}?service=99999")
        self.assertEqual(resp.status_code, 200)

    def test_post_valide_redirige_vers_succes(self):
        with self.settings(ANYMAIL={'BREVO_API_KEY': 'test'}):
            from unittest.mock import patch
            with patch('booking.views.send_mail'):
                resp = self.client.post(self.url, {
                    'customer_name': 'Marie',
                    'customer_email': 'marie@test.com',
                    'service': self.service.id,
                    'message': 'Test',
                })
        self.assertRedirects(resp, reverse('service_request_success'))

    def test_post_valide_cree_servicerequest_en_db(self):
        with self.settings(ANYMAIL={'BREVO_API_KEY': 'test'}):
            from unittest.mock import patch
            with patch('booking.views.send_mail'):
                self.client.post(self.url, {
                    'customer_name': 'Marie',
                    'customer_email': 'marie@test.com',
                    'service': self.service.id,
                    'message': '',
                })
        self.assertEqual(ServiceRequest.objects.count(), 1)
        req = ServiceRequest.objects.first()
        self.assertEqual(req.customer_name, 'Marie')
        self.assertEqual(req.service, self.service)

    def test_post_invalide_reaffiche_formulaire(self):
        resp = self.client.post(self.url, {
            'customer_name': '',
            'customer_email': 'bad',
            'service': self.service.id,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['form'].is_valid())

    def test_success_page_accessible(self):
        resp = self.client.get(reverse('service_request_success'))
        self.assertEqual(resp.status_code, 200)


# ══════════════════════════════════════════════════════════════════════════════
# 6. VUE booking_page — GET et filtre des services
# ══════════════════════════════════════════════════════════════════════════════

class BookingPageViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_page_accessible(self):
        resp = self.client.get(reverse('booking'))
        self.assertEqual(resp.status_code, 200)

    def test_services_affiches(self):
        make_service(name="Pose Lace HD")
        resp = self.client.get(reverse('booking'))
        self.assertContains(resp, 'Pose Lace HD')

    def test_bouton_reserver_pour_service_normal(self):
        make_service(name="Pose Perruque", sans_creneau=False)
        resp = self.client.get(reverse('booking'))
        self.assertContains(resp, 'Réserver')

    def test_bouton_demande_pour_service_depot(self):
        make_service(name="Coloration", sans_creneau=True)
        resp = self.client.get(reverse('booking'))
        self.assertContains(resp, 'Faire une demande')

    def test_services_ordonnes_par_order_field(self):
        make_service(name="Customisation", order=99)
        make_service(name="Pose Lace", order=0)
        resp = self.client.get(reverse('booking'))
        content = resp.content.decode()
        self.assertLess(content.index('Pose Lace'), content.index('Customisation'))
