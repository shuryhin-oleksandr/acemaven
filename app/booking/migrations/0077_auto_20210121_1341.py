# Generated by Django 3.1 on 2021-01-21 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0076_trackstatus_show_after_departure'),
    ]

    operations = [
        migrations.AddField(
            model_name='trackstatus',
            name='auto_add_on_actual_date_of_arrival',
            field=models.BooleanField(default=False, verbose_name='Add the status after adding actual date of arrival'),
        ),
        migrations.AddField(
            model_name='trackstatus',
            name='auto_add_on_actual_date_of_departure',
            field=models.BooleanField(default=False, verbose_name='Add the status after adding actual date of departure'),
        ),
    ]
