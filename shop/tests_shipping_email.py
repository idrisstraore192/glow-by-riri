"""
Tests pour l'envoi automatique d'email quand une commande est marquée expédiée.
On mocke l'ORM et super().save_model pour éviter toute dépendance à la base de données.
"""
from unittest.mock import patch, MagicMock
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, SimpleTestCase
from shop.admin import OrderAdmin


def make_order(pk=1, customer_name="Cliente Test", customer_email="cliente@test.com",
               shipped=False, tracking_number=""):
    order = MagicMock()
    order.pk = pk
    order.id = pk
    order.customer_name = customer_name
    order.customer_email = customer_email
    order.shipped = shipped
    order.tracking_number = tracking_number
    return order


class ShippingEmailTest(SimpleTestCase):

    def setUp(self):
        self.admin = OrderAdmin(MagicMock(), AdminSite())
        self.request = RequestFactory().post("/admin/")
        self.form = MagicMock()

    def _run_save(self, order, was_shipped_in_db=False, change=True):
        """Exécute save_model en mockant l'ORM et super()."""
        mock_qs = MagicMock()
        mock_qs.exists.return_value = was_shipped_in_db

        with patch("shop.admin.Order.objects.filter", return_value=mock_qs), \
             patch("django.contrib.admin.ModelAdmin.save_model"), \
             patch("shop.admin.send_mail") as mock_send:
            self.admin.save_model(self.request, order, self.form, change)
            return mock_send

    def _get_email_kwargs(self, mock_send):
        """Retourne les kwargs passés à send_mail."""
        return mock_send.call_args[1]

    # ── Cas où l'email DOIT être envoyé ──────────────────────────────────────

    def test_email_envoye_quand_shipped_passe_a_true(self):
        """Email envoyé quand une commande passe de non-expédiée à expédiée."""
        order = make_order(shipped=True)
        mock_send = self._run_save(order, was_shipped_in_db=False, change=True)
        mock_send.assert_called_once()

    def test_sujet_contient_id_et_nom_site(self):
        """Le sujet contient le numéro de commande et 'Glow by Riri'."""
        order = make_order(pk=42, shipped=True)
        mock_send = self._run_save(order, was_shipped_in_db=False)
        subject = self._get_email_kwargs(mock_send)["subject"]
        self.assertIn("42", subject)
        self.assertIn("Glow by Riri", subject)

    def test_email_envoye_a_la_bonne_adresse(self):
        """L'email est envoyé à l'adresse email de la cliente."""
        order = make_order(shipped=True, customer_email="marie@example.com")
        mock_send = self._run_save(order, was_shipped_in_db=False)
        recipient = self._get_email_kwargs(mock_send)["recipient_list"]
        self.assertIn("marie@example.com", recipient)

    def test_nom_cliente_dans_corps_email(self):
        """Le nom de la cliente apparaît dans le corps du mail."""
        order = make_order(shipped=True, customer_name="Marie Dupont")
        mock_send = self._run_save(order, was_shipped_in_db=False)
        body = self._get_email_kwargs(mock_send)["message"]
        self.assertIn("Marie Dupont", body)

    def test_lien_suivi_dans_corps_email(self):
        """Le lien vers /shop/suivi/ est présent dans l'email."""
        order = make_order(shipped=True)
        mock_send = self._run_save(order, was_shipped_in_db=False)
        body = self._get_email_kwargs(mock_send)["message"]
        self.assertIn("/shop/suivi/", body)

    def test_numero_suivi_dans_email_si_renseigne(self):
        """Le numéro de suivi apparaît dans l'email si Riri l'a saisi."""
        order = make_order(shipped=True, tracking_number="CA123456789")
        mock_send = self._run_save(order, was_shipped_in_db=False)
        body = self._get_email_kwargs(mock_send)["message"]
        self.assertIn("CA123456789", body)

    # ── Cas où l'email NE DOIT PAS être envoyé ───────────────────────────────

    def test_pas_email_si_deja_shipped_en_base(self):
        """Pas de double email si la commande était déjà expédiée en base."""
        order = make_order(shipped=True)
        mock_send = self._run_save(order, was_shipped_in_db=True, change=True)
        mock_send.assert_not_called()

    def test_pas_email_si_pas_shipped(self):
        """Pas d'email si shipped reste à False."""
        order = make_order(shipped=False)
        mock_send = self._run_save(order, was_shipped_in_db=False)
        mock_send.assert_not_called()

    def test_pas_email_sans_adresse_email(self):
        """Pas d'email si la commande n'a pas d'adresse email cliente."""
        order = make_order(shipped=True, customer_email="")
        mock_send = self._run_save(order, was_shipped_in_db=False)
        mock_send.assert_not_called()

    def test_sans_numero_suivi_pas_de_ligne_suivi(self):
        """Sans numéro de suivi, la ligne 'Numéro de suivi' n'apparaît pas."""
        order = make_order(shipped=True, tracking_number="")
        mock_send = self._run_save(order, was_shipped_in_db=False)
        body = self._get_email_kwargs(mock_send)["message"]
        self.assertNotIn("Numéro de suivi", body)
