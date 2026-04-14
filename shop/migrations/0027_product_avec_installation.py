from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0026_lacevariant_media'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='avec_installation',
            field=models.BooleanField(default=False, verbose_name='Option pose (-5%)', help_text="Afficher l'option 'Pose chez Glow by Riri' sur la fiche produit."),
        ),
    ]
