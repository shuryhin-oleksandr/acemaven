# Generated by Django 3.1 on 2020-09-21 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20200921_0735'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bankaccount',
            name='date',
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='date_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='asdads'),
        ),
    ]
