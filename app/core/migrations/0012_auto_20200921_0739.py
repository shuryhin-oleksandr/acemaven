# Generated by Django 3.1 on 2020-09-21 07:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_bankaccount_good'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bankaccount',
            name='date_updated',
        ),
        migrations.RemoveField(
            model_name='bankaccount',
            name='good',
        ),
    ]
