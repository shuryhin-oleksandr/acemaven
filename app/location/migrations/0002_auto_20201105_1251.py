# Generated by Django 3.1 on 2020-11-05 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='chosen_for_platform',
            field=models.BooleanField(default=False, verbose_name='Country was chosen as main for platform'),
        ),
        migrations.AlterField(
            model_name='country',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Country is active'),
        ),
        migrations.AlterField(
            model_name='state',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='State is active'),
        ),
    ]
