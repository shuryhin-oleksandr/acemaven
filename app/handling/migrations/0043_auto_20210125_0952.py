# Generated by Django 3.1 on 2021-01-25 09:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0042_auto_20210120_0924'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='billingexchangerate',
            options={'ordering': ['date']},
        ),
    ]
