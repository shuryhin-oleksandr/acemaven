# Generated by Django 3.1 on 2021-05-15 08:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0050_auto_20210515_0840'),
        ('location', '0005_auto_20210303_0915'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='country',
            options={'verbose_name': 'Country', 'verbose_name_plural': 'Countries'},
        ),
        migrations.AlterField(
            model_name='country',
            name='currency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='handling.currency', verbose_name='Currency'),
        ),
    ]
