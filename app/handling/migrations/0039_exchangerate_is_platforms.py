# Generated by Django 3.1 on 2021-01-04 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0038_pixapisetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchangerate',
            name='is_platforms',
            field=models.BooleanField(default=False, verbose_name='Is exchange rate of the platform'),
        ),
    ]
