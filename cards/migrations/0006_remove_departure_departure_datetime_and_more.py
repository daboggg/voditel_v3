# Generated by Django 5.1.1 on 2024-11-24 13:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0005_rename_return_time_datetime_departure_return_datetime'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='departure',
            name='departure_datetime',
        ),
        migrations.RemoveField(
            model_name='departure',
            name='return_datetime',
        ),
    ]
