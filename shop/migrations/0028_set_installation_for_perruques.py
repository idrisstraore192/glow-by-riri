from django.db import migrations


def enable_installation_for_perruques(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    Product.objects.filter(product_type='perruque').update(avec_installation=True)


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0027_product_avec_installation'),
    ]

    operations = [
        migrations.RunPython(enable_installation_for_perruques, migrations.RunPython.noop),
    ]
