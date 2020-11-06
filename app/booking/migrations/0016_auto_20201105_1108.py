# Generated by Django 3.1 on 2020-11-05 11:08

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0013_auto_20201103_1421'),
        ('booking', '0015_auto_20201104_1714'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='number_of_documents',
            field=models.PositiveIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Number of documents for chosen release type'),
        ),
        migrations.AddField(
            model_name='booking',
            name='release_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='handling.releasetype'),
        ),
    ]
