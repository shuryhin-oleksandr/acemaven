# Generated by Django 3.1 on 2020-11-26 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0044_auto_20201126_1037'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='aceid',
            field=models.CharField(max_length=8, null=True, verbose_name='Booking ACEID number'),
        ),
    ]
