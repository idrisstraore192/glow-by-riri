from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0025_add_lace_variant'),
    ]

    operations = [
        migrations.AddField(
            model_name='lacevariant',
            name='photo_url',
            field=models.URLField(blank=True, default='', verbose_name='Photo (Cloudinary)'),
        ),
        migrations.AddField(
            model_name='lacevariant',
            name='video_url',
            field=models.URLField(blank=True, default='', verbose_name='Vidéo (Cloudinary)'),
        ),
    ]
