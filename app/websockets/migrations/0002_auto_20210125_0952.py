# Generated by Django 3.1 on 2021-01-25 09:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('websockets', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chat',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['date_created']},
        ),
    ]
