# Generated by Django 3.1 on 2020-09-25 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_freightrate_rate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rate',
            name='surcharge',
        ),
        migrations.AddField(
            model_name='rate',
            name='surcharges',
            field=models.ManyToManyField(related_name='rates', to='booking.Surcharge'),
        ),
    ]
