from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0024_add_stock_slug_promocode_wishlist'),
    ]

    operations = [
        migrations.CreateModel(
            name='LaceVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_lace', models.CharField(
                    choices=[('transparente', 'Transparente'), ('hd', 'HD')],
                    max_length=20, verbose_name='Type'
                )),
                ('taille_lace', models.CharField(
                    choices=[('13x4', '13x4'), ('13x6', '13x6'), ('4x4', '4x4'), ('5x5', '5x5'), ('360', '360°')],
                    max_length=10, verbose_name='Taille'
                )),
                ('longueur', models.CharField(max_length=20, verbose_name='Longueur')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Prix')),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lace_variants',
                    to='shop.product',
                    verbose_name='Produit'
                )),
            ],
            options={
                'verbose_name': 'Variante lace',
                'verbose_name_plural': 'Variantes lace',
                'ordering': ['type_lace', 'taille_lace', 'longueur'],
                'unique_together': {('product', 'type_lace', 'taille_lace', 'longueur')},
            },
        ),
    ]
