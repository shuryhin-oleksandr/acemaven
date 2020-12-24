# Generated by Django 3.1 on 2020-12-23 12:02

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0034_auto_20201223_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seatrackingsetting',
            name='api_key',
            field=models.CharField(max_length=24, validators=[django.core.validators.RegexValidator(message='Invalid format. Must be: 0000-0000-0000-0000', regex='^(\\w|\\d){4}-(\\w|\\d){4}-(\\w|\\d){4}-(\\w|\\d){4}-(\\w|\\d){4}$')], verbose_name='Api key'),
        ),
    ]
