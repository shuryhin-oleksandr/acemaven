# Generated by Django 3.1 on 2020-11-02 11:05

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0012_auto_20201102_1101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='charge',
            name='charge',
            field=models.DecimalField(decimal_places=2, max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Charge amount'),
        ),
        migrations.AlterField(
            model_name='rate',
            name='rate',
            field=models.DecimalField(decimal_places=2, max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Rate amount'),
        ),
        migrations.AlterField(
            model_name='usagefee',
            name='charge',
            field=models.DecimalField(decimal_places=2, max_digits=15, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Charge amount'),
        ),
    ]
