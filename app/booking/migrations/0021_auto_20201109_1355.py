# Generated by Django 3.1 on 2020-11-09 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0020_auto_20201109_1319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cargogroup',
            name='frozen',
            field=models.CharField(choices=[('frozen', 'Frozen'), ('cold', 'Chilled')], max_length=10, null=True, verbose_name='Frozen or chilled cargo'),
        ),
    ]
