# Generated by Django 3.1 on 2020-12-16 11:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0024_auto_20201204_1214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalsetting',
            name='export_deadline_days',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Number of days that the agent will have to confirm a booking request(export)'),
        ),
        migrations.AlterField(
            model_name='generalsetting',
            name='import_deadline_days',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Number of days that the agent will have to confirm a booking request(import)'),
        ),
    ]
