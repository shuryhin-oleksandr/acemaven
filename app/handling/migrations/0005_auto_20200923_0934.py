# Generated by Django 3.1 on 2020-09-23 09:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0004_auto_20200916_0829'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='containertype',
            name='mode',
        ),
        migrations.AddField(
            model_name='containertype',
            name='shipping_mode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='container_types', to='handling.shippingmode'),
        ),
    ]
