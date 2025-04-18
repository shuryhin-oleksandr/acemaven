# Generated by Django 3.1 on 2020-11-08 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0018_auto_20201108_1332'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalsurcharge',
            name='is_document',
            field=models.BooleanField(default=False, verbose_name='Is document'),
        ),
        migrations.AddField(
            model_name='additionalsurcharge',
            name='is_handling',
            field=models.BooleanField(default=False, verbose_name='Is handling'),
        ),
        migrations.AddField(
            model_name='additionalsurcharge',
            name='is_other',
            field=models.BooleanField(default=False, verbose_name='Is other'),
        ),
    ]
