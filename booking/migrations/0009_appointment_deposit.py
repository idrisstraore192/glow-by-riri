from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0008_add_discount_percent'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='customer_email',
            field=models.EmailField(blank=True, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='deposit_paid',
            field=models.BooleanField(default=False, verbose_name='Acompte payé (20 $)'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='stripe_session_id',
            field=models.CharField(blank=True, max_length=200, verbose_name='Session Stripe'),
        ),
    ]
