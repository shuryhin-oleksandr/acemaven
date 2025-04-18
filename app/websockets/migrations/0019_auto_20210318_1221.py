# Generated by Django 3.1 on 2021-03-18 12:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('websockets', '0018_auto_20210217_1524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='action_path',
            field=models.CharField(choices=[('booking', 'Booking'), ('billing', 'Billing'), ('operation', 'Operation'), ('surcharge', 'Surcharge'), ('freight_rate', 'Freight Rate'), ('support', 'Support')], default='booking', max_length=20, verbose_name='Action path'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='section',
            field=models.CharField(choices=[('surcharges', 'Surcharges'), ('freight_rates', 'Freight Rates'), ('requests', 'Requests'), ('operations', 'Operations'), ('operations_import', 'Operations (Imports)'), ('operations_export', 'Operations (Exports)'), ('chats', 'Chats')], max_length=17, verbose_name='Section'),
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('operations', 'Operations'), ('requests', 'Requests'), ('billing', 'Billing'), ('rates_and_services', 'Rates and services')], default='requests', max_length=20, verbose_name='Categories')),
                ('topic', models.TextField(blank=True, verbose_name='Topic')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('status', models.CharField(choices=[('completed', 'Completed'), ('in_progress', 'In progress')], default='in_progress', max_length=20, verbose_name='Status')),
                ('aceid', models.CharField(max_length=20, null=True, verbose_name='Operation number')),
                ('chat', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='websockets.chat')),
            ],
        ),
    ]
