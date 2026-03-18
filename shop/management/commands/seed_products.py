from django.core.management.base import BaseCommand
from shop.models import Product


PRODUCTS = [
    {
        "name": "Lace Spray Invisible",
        "price": 16.00,
        "description": (
            "Spécialement conçu pour fixer ta lace (frontal ou closure) sans colle. "
            "Aide vos lace à se fondre correctement pour un rendu très naturel."
        ),
    },
    {
        "name": "Stick Wax",
        "price": 12.00,
        "description": (
            "Bâton de cire coiffant – Forte tenue & longue durée.\n"
            "Lisse et fixe instantanément les cheveux rebelles sans laisser de résidus blancs.\n"
            "Idéal pour aplatir les mèches, contrôler les frisottis et discipliner les cheveux cassés, "
            "tout en gardant un fini non gras.\n"
            "Convient à tous les types de cheveux.\n"
            "Format 75 g – parfait pour un usage quotidien ou en retouches."
        ),
    },
    {
        "name": "Hold Glue 38 ml",
        "price": 20.00,
        "description": (
            "Hold Glue – 38 ml\n"
            "La Hold Glue est une colle capillaire haute performance offrant une tenue extrême et durable. "
            "Sa formule avancée résiste à l'humidité et à la chaleur, tout en assurant un confort optimal.\n\n"
            "Caractéristiques :\n"
            "• Waterproof\n"
            "• Sans odeur\n"
            "• Non toxique\n"
            "• Convient aux peaux grasses et sensibles\n"
            "• Compatible Lace & Poly\n"
            "• Idéale frontales et closures\n\n"
            "La colle capillaire Glow by Riri garantit une adhérence fiable, sans irritation ni résidus, "
            "pour une pose sécurisée et un rendu naturel."
        ),
    },
    {
        "name": "Hold Glue 150 ml",
        "price": 50.00,
        "description": (
            "Hold Glue – 150 ml\n"
            "La Hold Glue est une colle capillaire haute performance offrant une tenue extrême et durable. "
            "Sa formule avancée résiste à l'humidité et à la chaleur, tout en assurant un confort optimal.\n\n"
            "Caractéristiques :\n"
            "• Waterproof\n"
            "• Sans odeur\n"
            "• Non toxique\n"
            "• Convient aux peaux grasses et sensibles\n"
            "• Compatible Lace & Poly\n"
            "• Idéale frontales et closures\n\n"
            "La colle capillaire Glow by Riri garantit une adhérence fiable, sans irritation ni résidus, "
            "pour une pose sécurisée et un rendu naturel."
        ),
    },
]


class Command(BaseCommand):
    help = "Ajoute les produits initiaux Glow by Riri"

    def handle(self, *args, **kwargs):
        created = 0
        for data in PRODUCTS:
            obj, is_new = Product.objects.get_or_create(
                name=data["name"],
                defaults={"price": data["price"], "description": data["description"]},
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"✓ {obj.name}"))
            else:
                self.stdout.write(f"— déjà existant : {obj.name}")

        self.stdout.write(self.style.SUCCESS(f"\n{created} produit(s) ajouté(s)."))
