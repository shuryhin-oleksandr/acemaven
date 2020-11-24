# Generated by Django 3.1 on 2020-11-24 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0040_auto_20201123_0933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(choices=[('confirmed', 'Booking confirmed'), ('accepted', 'Booking accepted'), ('received', 'Booking request received')], default='received', max_length=30, verbose_name='Booking confirmed or not'),
        ),
    ]
