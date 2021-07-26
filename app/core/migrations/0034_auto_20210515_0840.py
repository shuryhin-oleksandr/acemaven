# Generated by Django 3.1 on 2021-05-15 08:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0083_auto_20210515_0840'),
        ('core', '0033_emailnotificationsetting'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bankaccount',
            options={'verbose_name': 'Bank account', 'verbose_name_plural': 'Bank accounts'},
        ),
        migrations.AlterModelOptions(
            name='company',
            options={'verbose_name': 'Company', 'verbose_name_plural': 'Companies'},
        ),
        migrations.AlterModelOptions(
            name='emailnotificationsetting',
            options={'verbose_name': 'Email notification', 'verbose_name_plural': 'Email notifications'},
        ),
        migrations.AlterModelOptions(
            name='review',
            options={'ordering': ['reviewer__companies__name', '-date_created'], 'verbose_name': 'Review', 'verbose_name_plural': 'Reviews'},
        ),
        migrations.AlterModelOptions(
            name='role',
            options={'verbose_name': 'Role', 'verbose_name_plural': 'Roles'},
        ),
        migrations.AlterModelOptions(
            name='shipper',
            options={'verbose_name': 'Shipper', 'verbose_name_plural': 'Shippers'},
        ),
        migrations.AlterModelOptions(
            name='signuprequest',
            options={'verbose_name': 'Sign up request', 'verbose_name_plural': 'Sign up requests'},
        ),
        migrations.AlterModelOptions(
            name='signuptoken',
            options={'verbose_name': 'Sign up token', 'verbose_name_plural': 'Sign up tokens'},
        ),
        # migrations.AddField(
        #     model_name='company',
        #     name='disabled',
        #     field=models.BooleanField(default=False, verbose_name='Disable functionality'),
        # ),
        # migrations.AddField(
        #     model_name='customuser',
        #     name='language',
        #     field=models.CharField(choices=[('en', 'English'), ('es', 'Spanish'), ('pt', 'Portuguese')], default='en', max_length=6, verbose_name='Language'),
        # ),
        # migrations.AddField(
        #     model_name='customuser',
        #     name='username',
        #     field=models.TextField(blank=True, null=True),
        # ),
        migrations.AlterField(
            model_name='customuser',
            name='companies',
            field=models.ManyToManyField(related_name='users', through='core.Role', to='core.Company', verbose_name='Company'),
        ),
        migrations.AlterField(
            model_name='review',
            name='operation',
            field=models.OneToOneField(limit_choices_to=models.Q(status__in=('confirmed', 'canceled_by_client', 'canceled_by_agent', 'canceled_by_system')), on_delete=django.db.models.deletion.CASCADE, to='booking.booking', verbose_name='Operation'),
        ),
        migrations.AlterField(
            model_name='review',
            name='reviewer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Reviewer'),
        ),
        migrations.AlterField(
            model_name='role',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company', verbose_name='Company'),
        ),
        migrations.AlterField(
            model_name='role',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AlterField(
            model_name='signuptoken',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
