# Generated by Django 3.1 on 2021-03-01 11:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0078_trackstatus_auto_add_on_shipment_details_change'),
        ('core', '0033_emailnotificationsetting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='operation',
            field=models.OneToOneField(limit_choices_to=models.Q(status__in=('confirmed', 'canceled_by_client', 'canceled_by_agent', 'canceled_by_system')), on_delete=django.db.models.deletion.CASCADE, to='booking.booking'),
        ),
    ]
