# Generated by Django 3.1 on 2020-12-01 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0047_auto_20201201_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='payment_due_by',
            field=models.DateField(null=True, verbose_name='Payment due by date'),
        ),
    ]
