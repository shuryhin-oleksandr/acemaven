# Generated by Django 3.1 on 2020-09-08 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20200908_1203'),
    ]

    operations = [
        migrations.RenameField(
            model_name='signuptoken',
            old_name='company',
            new_name='user',
        ),
    ]
