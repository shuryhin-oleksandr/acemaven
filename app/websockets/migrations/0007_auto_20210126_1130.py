# Generated by Django 3.1 on 2021-01-26 11:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('websockets', '0006_auto_20210126_1119'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notificationseen',
            name='notification',
        ),
        migrations.RemoveField(
            model_name='notificationseen',
            name='user',
        ),
        migrations.DeleteModel(
            name='Notification',
        ),
        migrations.DeleteModel(
            name='NotificationSeen',
        ),
    ]
