# Generated by Django 3.1 on 2020-09-28 09:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0005_auto_20200923_0934'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='globalfee',
            name='title',
        ),
        migrations.RemoveField(
            model_name='localfee',
            name='title',
        ),
    ]
