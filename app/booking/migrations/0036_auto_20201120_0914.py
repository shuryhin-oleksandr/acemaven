# Generated by Django 3.1 on 2020-11-20 09:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0035_auto_20201120_0822'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='company',
        ),
        migrations.AddField(
            model_name='booking',
            name='client_contact_person',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to=settings.AUTH_USER_MODEL),
        ),
    ]
