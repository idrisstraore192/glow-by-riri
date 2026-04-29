"""
Tests automatiques — shop (cart, prix, remises, variantes, promo, vues)
Lance avec : python manage.py test shop
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from shop.models import Product, ProductVariant, LaceVariant, PromoCode, Order
from shop.cart import Cart


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_product(name="Perruque HD", price="150.00", discount=0, stock=None,
                 product_type="perruque", avec_installation=False):
    return Product.objects.create(
        name=name,
        price=Decimal(price),
        discount_percent=Decimal(str(discount)),
        stock=stock,
        product_type=product_type,
        avec_installation=avec_installation,
    )


def make_lace_variant(product, type_lace="hd", taille="13x4",
                      longueur="16 pouces", price="200.00", stock=None):
    return LaceVariant.objects.create(
        product=product,
        type_lace=type_lace,
        taille_lace=taille,
        longueur=longueur,
        price=Decimal(price),
        stock=stock,
    )


def make_variant(product, label="16 pouces", price="180.00", stock=None):
    return ProductVariant.objects.create(
        product=product,
        variant_type="longueur",
        label=label,
        price=Decimal(price),
        stock=stock,
    )


class FakeSession(dict):
    """Session dict minimal pour Cart."""
    modified = False

    def setdefault(self, key, default):
        if key not in self:
            self[key] = default
        return self[key]


def make_cart(session=None):
    request = MagicMock()
    request.session = session or FakeSession()
    return Cart(request)


# ══════════════════════════════════════════════════════════════════════════════
# 1. MODÈLE PRODUCT — final_price
# ══════════════════════════════════════════════════════════════════════════════

class ProductFinalPriceTest(TestCase):

    def test_prix_sans_remise(self):
        p = make_product(price="100.00", discount=0)
        self.assertEqual(p.final_price, 100.0)

    def test_prix_avec_20_pourcent(self):
        p = make_product(price="100.00", discount=20)
        self.assertEqual(p.final_price, 80.0)

    def test_prix_avec_remise_decimale(self):
        p = make_product(price="150.00", discount=15)
        self.assertAlmostEqual(p.final_price, 127.5, places=2)

    def test_prix_remise_zero_retourne_prix_base(self):
        p = make_product(price="200.00", discount=0)
        self.assertEqual(p.final_price, 200.0)


# ══════════════════════════════════════════════════════════════════════════════
# 2. CART — clés, prix stockés, cumul de quantité
# ══════════════════════════════════════════════════════════════════════════════

class CartAddSimpleTest(TestCase):

    def test_cle_produit_simple(self):
        p = make_product()
        cart = make_cart()
        cart.add(p)
        self.assertIn(str(p.id), cart.cart)

    def test_prix_stocke_sans_remise(self):
        p = make_product(price="100.00", discount=0)
        cart = make_cart()
        cart.add(p)
        self.assertEqual(float(cart.cart[str(p.id)]['price']), 100.0)

    def test_prix_stocke_avec_remise(self):
        p = make_product(price="100.00", discount=20)
        cart = make_cart()
        cart.add(p)
        self.assertEqual(float(cart.cart[str(p.id)]['price']), 80.0)

    def test_cumul_quantite_meme_cle(self):
        p = make_product()
        cart = make_cart()
        cart.add(p, quantity=1)
        cart.add(p, quantity=2)
        self.assertEqual(cart.cart[str(p.id)]['quantity'], 3)

    def test_longueur_cart(self):
        p = make_product()
        cart = make_cart()
        cart.add(p, quantity=3)
        self.assertEqual(len(cart), 3)

    def test_total_cart(self):
        p = make_product(price="100.00", discount=0)
        cart = make_cart()
        cart.add(p, quantity=2)
        self.assertAlmostEqual(cart.get_total(), 200.0, places=2)


class CartAddVariantTest(TestCase):

    def test_cle_avec_variant(self):
        p = make_product()
        v = make_variant(p, price="180.00")
        cart = make_cart()
        cart.add(p, variant=v)
        expected_key = f"{p.id}_{v.id}"
        self.assertIn(expected_key, cart.cart)

    def test_prix_variant_sans_remise(self):
        p = make_product(price="150.00", discount=0)
        v = make_variant(p, price="180.00")
        cart = make_cart()
        cart.add(p, variant=v)
        key = f"{p.id}_{v.id}"
        self.assertEqual(float(cart.cart[key]['price']), 180.0)

    def test_prix_variant_avec_remise_produit(self):
        p = make_product(price="150.00", discount=20)
        v = make_variant(p, price="200.00")
        cart = make_cart()
        cart.add(p, variant=v)
        key = f"{p.id}_{v.id}"
        # 200 * (1 - 0.20) = 160
        self.assertAlmostEqual(float(cart.cart[key]['price']), 160.0, places=2)


class CartAddLaceVariantTest(TestCase):

    def test_cle_lace_variant(self):
        p = make_product()
        lv = make_lace_variant(p, type_lace="hd", taille="13x4", longueur="16 pouces", price="220.00")
        cart = make_cart()
        cart.add(p, lace_variant=lv)
        expected_key = f"{p.id}_lv_hd_13x4_16 pouces"
        self.assertIn(expected_key, cart.cart)

    def test_prix_lace_sans_remise(self):
        p = make_product(price="100.00", discount=0)
        lv = make_lace_variant(p, price="220.00")
        cart = make_cart()
        cart.add(p, lace_variant=lv)
        key = f"{p.id}_lv_{lv.type_lace}_{lv.taille_lace}_{lv.longueur}"
        self.assertEqual(float(cart.cart[key]['price']), 220.0)

    def test_prix_lace_avec_remise(self):
        p = make_product(discount=10)
        lv = make_lace_variant(p, price="200.00")
        cart = make_cart()
        cart.add(p, lace_variant=lv)
        key = f"{p.id}_lv_{lv.type_lace}_{lv.taille_lace}_{lv.longueur}"
        # 200 * 0.90 = 180
        self.assertAlmostEqual(float(cart.cart[key]['price']), 180.0, places=2)


class CartInstallationTest(TestCase):

    def test_cle_avec_pose(self):
        p = make_product()
        cart = make_cart()
        cart.add(p, with_installation=True)
        key = f"{p.id}_pose"
        self.assertIn(key, cart.cart)

    def test_cle_sans_pose_distincte_de_avec_pose(self):
        p = make_product()
        cart = make_cart()
        cart.add(p, with_installation=False)
        cart.add(p, with_installation=True)
        self.assertEqual(len(cart.cart), 2)

    def test_prix_pose_moins_5_pourcent(self):
        p = make_product(price="200.00", discount=0)
        cart = make_cart()
        cart.add(p, with_installation=True)
        key = f"{p.id}_pose"
        # 200 * 0.95 = 190
        self.assertAlmostEqual(float(cart.cart[key]['price']), 190.0, places=2)

    def test_prix_pose_sur_prix_deja_remise(self):
        # remise 20% d'abord, puis -5% pose
        p = make_product(price="200.00", discount=20)
        cart = make_cart()
        cart.add(p, with_installation=True)
        key = f"{p.id}_pose"
        # 200 * 0.80 = 160, puis 160 * 0.95 = 152
        self.assertAlmostEqual(float(cart.cart[key]['price']), 152.0, places=2)

    def test_pose_sur_lace_variant_avec_remise(self):
        p = make_product(discount=10)
        lv = make_lace_variant(p, price="200.00")
        cart = make_cart()
        cart.add(p, lace_variant=lv, with_installation=True)
        key = f"{p.id}_lv_{lv.type_lace}_{lv.taille_lace}_{lv.longueur}_pose"
        # 200 * 0.90 = 180, puis 180 * 0.95 = 171
        self.assertAlmostEqual(float(cart.cart[key]['price']), 171.0, places=2)


class CartRemoveUpdateTest(TestCase):

    def test_remove_par_cle(self):
        p = make_product()
        cart = make_cart()
        cart.add(p)
        cart.remove(p, item_key=str(p.id))
        self.assertNotIn(str(p.id), cart.cart)

    def test_update_quantite(self):
        p = make_product()
        cart = make_cart()
        cart.add(p, quantity=1)
        cart.update(p, quantity=5, item_key=str(p.id))
        self.assertEqual(cart.cart[str(p.id)]['quantity'], 5)

    def test_update_zero_supprime_entree(self):
        p = make_product()
        cart = make_cart()
        cart.add(p)
        cart.update(p, quantity=0, item_key=str(p.id))
        self.assertNotIn(str(p.id), cart.cart)

    def test_total_multi_produits(self):
        p1 = make_product(price="100.00", discount=0)
        p2 = make_product(name="Produit 2", price="50.00", discount=0)
        cart = make_cart()
        cart.add(p1, quantity=2)
        cart.add(p2, quantity=1)
        self.assertAlmostEqual(cart.get_total(), 250.0, places=2)


# ══════════════════════════════════════════════════════════════════════════════
# 3. PROMO CODES
# ══════════════════════════════════════════════════════════════════════════════

class PromoCodeIsValidTest(TestCase):

    def test_code_actif_valide(self):
        promo = PromoCode.objects.create(code="TEST10", discount_percent=10, active=True)
        valid, msg = promo.is_valid()
        self.assertTrue(valid)

    def test_code_inactif(self):
        promo = PromoCode.objects.create(code="INACTIF", discount_percent=10, active=False)
        valid, _ = promo.is_valid()
        self.assertFalse(valid)

    def test_code_expire(self):
        promo = PromoCode.objects.create(
            code="EXPIRE",
            discount_percent=10,
            active=True,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        valid, _ = promo.is_valid()
        self.assertFalse(valid)

    def test_code_pas_encore_expire(self):
        promo = PromoCode.objects.create(
            code="FUTUR",
            discount_percent=10,
            active=True,
            expires_at=timezone.now() + timezone.timedelta(days=1),
        )
        valid, _ = promo.is_valid()
        self.assertTrue(valid)

    def test_max_uses_atteint(self):
        promo = PromoCode.objects.create(
            code="MAXUSE", discount_percent=10, active=True,
            max_uses=5, uses_count=5,
        )
        valid, _ = promo.is_valid()
        self.assertFalse(valid)

    def test_max_uses_pas_encore_atteint(self):
        promo = PromoCode.objects.create(
            code="RESTANT", discount_percent=10, active=True,
            max_uses=5, uses_count=4,
        )
        valid, _ = promo.is_valid()
        self.assertTrue(valid)

    def test_sans_limite_dutilisation(self):
        promo = PromoCode.objects.create(
            code="ILLIMITE", discount_percent=10, active=True,
            max_uses=None, uses_count=9999,
        )
        valid, _ = promo.is_valid()
        self.assertTrue(valid)


# ══════════════════════════════════════════════════════════════════════════════
# 4. VUE apply_promo
# ══════════════════════════════════════════════════════════════════════════════

class ApplyPromoViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('apply_promo')

    def test_code_valide_retourne_remise(self):
        PromoCode.objects.create(code="PROMO20", discount_percent=20, active=True)
        resp = self.client.post(
            self.url, data=json.dumps({'code': 'PROMO20'}),
            content_type='application/json'
        )
        data = resp.json()
        self.assertTrue(data['valid'])
        self.assertEqual(data['discount'], 20.0)

    def test_code_valide_enregistre_en_session(self):
        PromoCode.objects.create(code="SAVE10", discount_percent=10, active=True)
        self.client.post(
            self.url, data=json.dumps({'code': 'SAVE10'}),
            content_type='application/json'
        )
        session = self.client.session
        self.assertEqual(session.get('promo_code'), 'SAVE10')

    def test_code_inexistant(self):
        resp = self.client.post(
            self.url, data=json.dumps({'code': 'FAUX'}),
            content_type='application/json'
        )
        self.assertFalse(resp.json()['valid'])

    def test_code_inactif(self):
        PromoCode.objects.create(code="DESAC", discount_percent=10, active=False)
        resp = self.client.post(
            self.url, data=json.dumps({'code': 'DESAC'}),
            content_type='application/json'
        )
        self.assertFalse(resp.json()['valid'])

    def test_code_vide(self):
        resp = self.client.post(
            self.url, data=json.dumps({'code': ''}),
            content_type='application/json'
        )
        self.assertFalse(resp.json()['valid'])

    def test_methode_get_refusee(self):
        resp = self.client.get(self.url)
        self.assertFalse(resp.json()['valid'])


# ══════════════════════════════════════════════════════════════════════════════
# 5. VUE add_to_cart
# ══════════════════════════════════════════════════════════════════════════════

class AddToCartViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_ajout_produit_simple(self):
        p = make_product(stock=None)
        url = reverse('add_to_cart', args=[p.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.client.session['cart'][str(p.id)]['quantity'], 1)

    def test_stock_zero_refuse(self):
        p = make_product(stock=0)
        url = reverse('add_to_cart', args=[p.id])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(resp.json()['ok'])

    def test_lace_incomplet_refuse(self):
        p = make_product()
        make_lace_variant(p)
        url = reverse('add_to_cart', args=[p.id])
        resp = self.client.post(url, {'lace_type': 'hd'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(resp.json()['ok'])

    def test_lace_complet_accepte(self):
        p = make_product()
        lv = make_lace_variant(p, type_lace='hd', taille='13x4', longueur='16 pouces')
        url = reverse('add_to_cart', args=[p.id])
        resp = self.client.post(url, {
            'lace_type': 'hd', 'lace_taille': '13x4', 'lace_longueur': '16 pouces',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(resp.json()['ok'])

    def test_ajout_ajax_retourne_cart_count(self):
        p = make_product()
        url = reverse('add_to_cart', args=[p.id])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn('cart_count', resp.json())
        self.assertEqual(resp.json()['cart_count'], 1)

    def test_produit_avec_variante_requiert_variant_id(self):
        p = make_product()
        make_variant(p)
        url = reverse('add_to_cart', args=[p.id])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(resp.json()['ok'])

    def test_lace_stock_zero_refuse(self):
        p = make_product()
        make_lace_variant(p, type_lace='hd', taille='13x4', longueur='16 pouces', stock=0)
        url = reverse('add_to_cart', args=[p.id])
        resp = self.client.post(url, {
            'lace_type': 'hd', 'lace_taille': '13x4', 'lace_longueur': '16 pouces',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(resp.json()['ok'])


# ══════════════════════════════════════════════════════════════════════════════
# 6. CHECKOUT — recalcul des prix côté serveur
# ══════════════════════════════════════════════════════════════════════════════

class CheckoutPriceTest(TestCase):
    """
    Vérifie que le checkout recalcule les prix depuis la base de données
    et ne fait pas confiance aux prix du panier côté client.
    """

    def _checkout_line_items(self, session_data):
        """Lance le checkout et capture les line_items envoyés à Stripe."""
        client = Client()
        # Properly persist session before the request
        session = client.session
        for k, v in session_data.items():
            session[k] = v
        session.save()

        captured = {}

        def fake_stripe_create(**kwargs):
            captured['line_items'] = kwargs.get('line_items', [])
            mock_session = MagicMock()
            mock_session.url = 'https://stripe.com/pay/fake'
            return mock_session

        with patch('shop.views.stripe.checkout.Session.create', side_effect=fake_stripe_create), \
             patch('shop.views.stripe.Coupon.create', return_value=MagicMock(id='coupon_id')):
            client.get(reverse('checkout'))

        return captured.get('line_items', [])

    def test_prix_produit_simple_recalcule(self):
        p = make_product(price="100.00", discount=0)
        session = {'cart': {str(p.id): {'quantity': 1, 'price': '1.00', 'product_id': p.id, 'label': None, 'lace_label': None, 'type_lace_label': None, 'installation': False}}}
        items = self._checkout_line_items(session)
        self.assertEqual(len(items), 1)
        # Doit recalculer depuis la DB, pas utiliser le prix tampered "1.00"
        self.assertEqual(items[0]['price_data']['unit_amount'], 10000)  # 100.00$

    def test_prix_avec_remise_recalcule(self):
        p = make_product(price="200.00", discount=20)
        session = {'cart': {str(p.id): {'quantity': 1, 'price': '999.00', 'product_id': p.id, 'label': None, 'lace_label': None, 'type_lace_label': None, 'installation': False}}}
        items = self._checkout_line_items(session)
        self.assertEqual(len(items), 1)
        # 200 * 0.80 = 160.00$ = 16000 centimes
        self.assertEqual(items[0]['price_data']['unit_amount'], 16000)

    def test_prix_avec_pose_recalcule(self):
        p = make_product(price="200.00", discount=0)
        key = f"{p.id}_pose"
        session = {'cart': {key: {'quantity': 1, 'price': '999.00', 'product_id': p.id, 'label': None, 'lace_label': None, 'type_lace_label': None, 'installation': True}}}
        items = self._checkout_line_items(session)
        self.assertEqual(len(items), 1)
        # 200 * 0.95 = 190.00$ = 19000 centimes
        self.assertEqual(items[0]['price_data']['unit_amount'], 19000)

    def test_prix_lace_variant_recalcule(self):
        p = make_product(discount=10)
        lv = make_lace_variant(p, type_lace='hd', taille='13x4', longueur='16 pouces', price="200.00")
        key = f"{p.id}_lv_hd_13x4_16 pouces"
        session = {'cart': {key: {'quantity': 1, 'price': '999.00', 'product_id': p.id, 'label': None, 'lace_label': None, 'type_lace_label': None, 'installation': False}}}
        items = self._checkout_line_items(session)
        self.assertEqual(len(items), 1)
        # 200 * 0.90 = 180.00$ = 18000 centimes
        self.assertEqual(items[0]['price_data']['unit_amount'], 18000)

    def test_prix_variant_simple_recalcule(self):
        p = make_product(price="100.00", discount=20)
        v = make_variant(p, price="200.00")
        key = f"{p.id}_{v.id}"
        session = {'cart': {key: {'quantity': 1, 'price': '999.00', 'product_id': p.id, 'label': '16 pouces', 'lace_label': None, 'type_lace_label': None, 'installation': False}}}
        items = self._checkout_line_items(session)
        self.assertEqual(len(items), 1)
        # variant 200 * 0.80 = 160.00$ = 16000 centimes
        self.assertEqual(items[0]['price_data']['unit_amount'], 16000)

    def test_panier_vide_redirige(self):
        resp = self.client.get(reverse('checkout'))
        self.assertRedirects(resp, reverse('products'))


# ══════════════════════════════════════════════════════════════════════════════
# 7. VUE cart_view — affichage promo
# ══════════════════════════════════════════════════════════════════════════════

class CartViewPromoTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.product = make_product(price="100.00", discount=0)

    def _add_to_cart(self):
        self.client.post(reverse('add_to_cart', args=[self.product.id]))

    def test_total_sans_promo(self):
        self._add_to_cart()
        resp = self.client.get(reverse('cart'))
        self.assertContains(resp, '100')

    def test_promo_appliquee_correctement(self):
        PromoCode.objects.create(code="RIRI10", discount_percent=10, active=True)
        self._add_to_cart()
        self.client.post(
            reverse('apply_promo'),
            data=json.dumps({'code': 'RIRI10'}),
            content_type='application/json',
        )
        resp = self.client.get(reverse('cart'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('90', resp.content.decode())

    def test_checkout_review_vide_redirige(self):
        resp = self.client.get(reverse('checkout_review'))
        self.assertRedirects(resp, reverse('products'))


# ══════════════════════════════════════════════════════════════════════════════
# 8. VUE product_list — ordre d'affichage
# ══════════════════════════════════════════════════════════════════════════════

class ProductListOrderTest(TestCase):

    def test_ordre_type_produit(self):
        perruque = make_product(name="Perruque A", product_type="perruque")
        produit = make_product(name="Shampoing", product_type="produit")
        bundle = make_product(name="Bundle XL", product_type="bundle")
        resp = self.client.get(reverse('products'))
        # Vérifier l'ordre dans le queryset du contexte, pas dans le HTML
        # (la nav HTML contient aussi "Bundle" donc index() serait trompeur)
        names = [p.name for p in resp.context['products']]
        self.assertLess(names.index('Shampoing'), names.index('Perruque A'))
        self.assertLess(names.index('Perruque A'), names.index('Bundle XL'))

    def test_filtre_categorie_perruques(self):
        perruque = make_product(name="Perruque HD", product_type="perruque")
        produit = make_product(name="Shampoing", product_type="produit")
        resp = self.client.get(reverse('products') + '?category=perruques')
        content = resp.content.decode()
        self.assertIn('Perruque HD', content)
        self.assertNotIn('Shampoing', content)

    def test_produit_indisponible_masque(self):
        p = make_product(name="Cache", product_type="produit")
        p.disponible = False
        p.save()
        resp = self.client.get(reverse('products'))
        self.assertNotIn('Cache', resp.content.decode())
