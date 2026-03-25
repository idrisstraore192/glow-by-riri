from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0018_add_tutorial_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='order',
            field=models.PositiveIntegerField(
                default=0,
                verbose_name="Ordre d'affichage",
                help_text="0 = en premier. Plus le chiffre est grand, plus le produit apparaît en bas."
            ),
        ),
    ]
