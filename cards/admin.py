from django.contrib import admin

from cards.models import Truck, Norm, Card, Departure


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    fields = ['name', 'full_name', 'number']


@admin.register(Norm)
class NormAdmin(admin.ModelAdmin):
    fields = ['season',
              'liter_per_km',
              'work_with_pump_liter_per_min',
              'work_without_pump_liter_per_min', ]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    fields = ['month', 'mileage', 'remaining_fuel', 'truck', 'norm']


@admin.register(Departure)
class DepartureAdmin(admin.ModelAdmin):
    fields = [
        'date',
        'departure_time',
        'return_time',
        'place_of_work',
        'distance',
        'mileage_end',
        'with_pump',
        'without_pump',
        'refueled',
        'card',
        'user',
        'norm',
    ]
