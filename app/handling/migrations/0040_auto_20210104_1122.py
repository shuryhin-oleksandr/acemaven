# Generated by Django 3.1 on 2021-01-04 11:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_auto_20201202_1321'),
        ('handling', '0039_exchangerate_is_platforms'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingExchangeRate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True, verbose_name='Exchange rate date')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exchange_rates', to='core.company')),
            ],
        ),
        migrations.AddField(
            model_name='exchangerate',
            name='billing_exchange_rate',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rates', to='handling.billingexchangerate'),
        ),
    ]
