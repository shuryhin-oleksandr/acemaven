# Generated by Django 3.1 on 2020-12-16 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0059_track'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cargogroup',
            name='volume',
            field=models.PositiveIntegerField(null=True, verbose_name='Number of items'),
        ),
    ]
