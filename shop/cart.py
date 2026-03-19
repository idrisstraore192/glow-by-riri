from .models import Product

CART_SESSION_KEY = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(CART_SESSION_KEY, {})

    def add(self, product, quantity=1, variant=None):
        key = f"{product.id}_{variant.id}" if variant else str(product.id)
        price = str(variant.price) if variant else str(product.price)
        size = variant.size if variant else None
        if key in self.cart:
            self.cart[key]['quantity'] += quantity
        else:
            self.cart[key] = {
                'quantity': quantity,
                'price': price,
                'product_id': product.id,
                'size': size,
            }
        self.save()

    def update(self, product, quantity):
        pid = str(product.id)
        if pid in self.cart:
            if quantity > 0:
                self.cart[pid]['quantity'] = quantity
            else:
                del self.cart[pid]
            self.save()

    def remove(self, product):
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.session.modified = True

    def __iter__(self):
        product_ids = [item['product_id'] for item in self.cart.values()]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        for item in self.cart.values():
            item = item.copy()
            item['product'] = products.get(item['product_id'])
            item['total'] = float(item['price']) * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total(self):
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())
