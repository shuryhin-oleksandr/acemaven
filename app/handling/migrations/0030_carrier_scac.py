# Generated by Django 3.1 on 2020-12-23 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('handling', '0029_auto_20201217_1215'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrier',
            name='scac',
            field=models.CharField(max_length=4, null=True, verbose_name='SCAC code'),
        ),
    ]
