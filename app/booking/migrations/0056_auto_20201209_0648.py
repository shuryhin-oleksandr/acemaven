# Generated by Django 3.1 on 2020-12-09 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0055_auto_20201208_1615'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(choices=[('confirmed', 'Booking Confirmed'), ('accepted', 'Booking Request in Progress'), ('received', 'Booking Request Received'), ('pending', 'Booking Fee Pending'), ('rejected', 'Booking Request Rejected'), ('canceled_by_agent', 'Operation Canceled by Agent'), ('canceled_by_client', 'Operation Canceled by Client'), ('completed', 'Operation Complete')], default='pending', max_length=30, verbose_name='Booking confirmed or not'),
        ),
    ]
