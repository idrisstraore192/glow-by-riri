from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0009_appointment_deposit'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailabilitySlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Date')),
                ('time', models.TimeField(verbose_name='Heure')),
                ('is_booked', models.BooleanField(default=False, verbose_name='Réservé')),
            ],
            options={
                'verbose_name': 'Créneau disponible',
                'verbose_name_plural': 'Créneaux disponibles',
                'ordering': ['date', 'time'],
                'unique_together': {('date', 'time')},
            },
        ),
        migrations.AddField(
            model_name='appointment',
            name='slot',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='booking.availabilityslot',
                verbose_name='Créneau',
            ),
        ),
    ]
