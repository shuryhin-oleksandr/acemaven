# Generated by Django 3.1 on 2020-10-07 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0009_auto_20201007_1130'),
    ]

    operations = [
        migrations.AddField(
            model_name='freightrate',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Freight rate is active or paused'),
        ),
    ]
