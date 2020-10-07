# Generated by Django 3.1 on 2020-10-07 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0008_auto_20201005_0811'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='surcharge',
            name='carrier_disclosure',
        ),
        migrations.AddField(
            model_name='freightrate',
            name='carrier_disclosure',
            field=models.BooleanField(default=False, verbose_name='Whether carrier name disclosed or not'),
        ),
    ]
