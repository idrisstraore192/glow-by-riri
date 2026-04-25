from .models import Product

CART_SESSION_KEY = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(CART_SESSION_KEY, {})

    def add(self, product, quantity=1, variant=None, with_installation=False, lace_label=None, type_lace_label=None, lace_variant=None):
        if lace_variant:
            type_display = dict(lace_variant.TYPE_CHOICES).get(lace_variant.type_lace, lace_variant.type_lace)
            label = f"{type_display} · {lace_variant.taille_lace} · {lace_variant.longueur}"
            key = f"{product.id}_lv_{lace_variant.type_lace}_{lace_variant.taille_lace}_{lace_variant.longueur}"
            base_price = float(lace_variant.price)
        else:
            key = f"{product.id}_{variant.id}" if variant else str(product.id)
            base_price = float(variant.price) if (variant and variant.price) else float(product.price)
            label = variant.label if variant else None
        if product.discount_percent and product.discount_percent > 0:
            base_price = round(base_price * (1 - float(product.discount_percent) / 100), 2)
        if with_installation:
            base_price = round(base_price * 0.95, 2)
        if key in self.cart:
            self.cart[key]['quantity'] += quantity
        else:
            self.cart[key] = {
                'quantity': quantity,
                'price': str(base_price),
                'product_id': product.id,
                'label': label,
                'lace_label': lace_label,
                'type_lace_label': type_lace_label,
                'installation': with_installation,
            }
        self.save()

    def update(self, product, quantity, item_key=None):
        key = item_key or str(product.id)
        if key in self.cart:
            if quantity > 0:
                self.cart[key]['quantity'] = quantity
            else:
                del self.cart[key]
            self.save()

    def remove(self, product, item_key=None):
        key = item_key or str(product.id)
        if key in self.cart:
            del self.cart[key]
            self.save()
        else:
            # fallback: remove all entries for this product
            keys = [k for k, v in self.cart.items() if v['product_id'] == product.id]
            for k in keys:
                del self.cart[k]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.session.modified = True

    def __iter__(self):
        product_ids = [item['product_id'] for item in self.cart.values()]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        for key, item in self.cart.items():
            item = item.copy()
            item['key'] = key
            item['product'] = products.get(item['product_id'])
            item['total'] = float(item['price']) * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total(self):
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())
