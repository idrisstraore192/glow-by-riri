from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1,1),(2,2),(3,3),(4,4),(5,5)], verbose_name='Note')),
                ('comment', models.TextField(verbose_name='Commentaire')),
                ('approved', models.BooleanField(default=False, verbose_name='Approuvé')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
            ],
            options={'verbose_name': 'Avis', 'verbose_name_plural': 'Avis', 'ordering': ['-created_at']},
        ),
    ]
