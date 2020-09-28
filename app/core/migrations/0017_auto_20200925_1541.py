# Generated by Django 3.1 on 2020-09-25 15:41

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20200924_1359'),
    ]

    operations = [
        migrations.RenameField(
            model_name='signuprequest',
            old_name='master_email',
            new_name='email',
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='first_name',
            field=models.CharField(max_length=150, null=True, verbose_name='Master first name'),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='last_name',
            field=models.CharField(max_length=150, null=True, verbose_name='Master last name'),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='master_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=13, null=True, region=None, verbose_name='Master phone number'),
        ),
        migrations.AddField(
            model_name='signuprequest',
            name='position',
            field=models.CharField(max_length=100, null=True, verbose_name='Master position in company'),
        ),
    ]
