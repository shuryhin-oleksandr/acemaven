# Generated by Django 3.1 on 2020-11-05 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0016_auto_20201105_1108'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalsurcharge',
            name='is_cold',
            field=models.BooleanField(default=False, verbose_name='Is cold'),
        ),
        migrations.AddField(
            model_name='additionalsurcharge',
            name='is_dangerous',
            field=models.BooleanField(default=False, verbose_name='Is dangerous'),
        ),
    ]
