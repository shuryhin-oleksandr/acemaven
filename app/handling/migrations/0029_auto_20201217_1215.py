# Generated by Django 3.1 on 2020-12-17 12:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0028_auto_20201217_1151'),
    ]

    operations = [
        migrations.RenameField(
            model_name='airtrackingsetting',
            old_name='username',
            new_name='user',
        ),
    ]
