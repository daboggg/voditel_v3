# Generated by Django 5.1.1 on 2024-11-24 16:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0007_departure_departure_datetime_and_more'),
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
