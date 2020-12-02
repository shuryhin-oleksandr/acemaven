# Generated by Django 3.1 on 2020-12-02 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0021_auto_20201116_1642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalsetting',
            name='show_freight_forwarder_name',
            field=models.CharField(choices=[('after_booking', 'Show after booking is paid'), ('all', 'Show in search results and after'), ('in_operation', 'Show only on operation page')], default='after_booking', max_length=50, verbose_name='Hide/show freight forwarder'),
        ),
    ]
