# Generated by Django 3.1 on 2020-11-18 19:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0032_quote_charges'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quote',
            name='charges',
            field=models.JSONField(null=True, verbose_name='Charges calculations'),
        ),
    ]
