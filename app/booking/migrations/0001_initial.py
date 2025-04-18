# Generated by Django 3.1 on 2020-09-21 06:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('handling', '0004_auto_20200916_0829'),
        ('core', '0007_bankaccount_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='Surcharge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.CharField(max_length=6, verbose_name='Surcharge direction, whether import or export')),
                ('start_date', models.DateField(verbose_name='Surcharge start date')),
                ('expiration_date', models.DateField(verbose_name='Surcharge expiration date')),
                ('carrier_disclosure', models.BooleanField(default=False, verbose_name='Whether carrier name disclosed or not')),
                ('carrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='surcharges', to='handling.carrier')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='surcharges', to='core.company')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='handling.port')),
                ('shipping_mode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='surcharges', to='handling.shippingmode')),
            ],
        ),
    ]
