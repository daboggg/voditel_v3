import datetime

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from users.templatetags.common_filters import get_rus_month_year
from django.utils import timezone


class Truck(models.Model):
    name = models.CharField(max_length=20, verbose_name="марка автомобиля")
    full_name = models.CharField(max_length=30, verbose_name="полное название автомобиля")
    number = models.CharField(max_length=20, verbose_name="номер автомобиля")

    def __str__(self):
        return f'{self.name} - {self.number}'


class Norm(models.Model):
    season = models.CharField(max_length=20, verbose_name="марка авто и сезон")
    liter_per_km = models.DecimalField(max_digits=4, decimal_places=3, verbose_name="пробег (л/км)")
    work_with_pump_liter_per_min = models.DecimalField(max_digits=4, decimal_places=3, verbose_name="работа с насосом (л/мин)")
    work_without_pump_liter_per_min = models.DecimalField(max_digits=4, decimal_places=3, verbose_name="работа без насоса (л/мин)")

    def __str__(self):
        return f'{self.season}'


class Card(models.Model):
    month = models.DateField(verbose_name="дата начала карты")
    mileage = models.PositiveIntegerField(verbose_name="пробег на 1 число месяца")
    remaining_fuel = models.DecimalField(max_digits=6, decimal_places=3, verbose_name="остаток топлива на 1 число месяца")
    truck = models.ForeignKey(Truck, related_name="cards", on_delete=models.CASCADE, verbose_name='автомобиль')
    norm = models.ForeignKey(Norm, related_name="cards", on_delete=models.CASCADE, verbose_name='норма расхода топлива')

    def __str__(self):
        return f'{self.truck.name} - {get_rus_month_year(self.month)}'

    def get_absolute_url(self):
        return reverse('card_detail', kwargs={'pk': self.id})

    class Meta:
        ordering = ["-month"]


class Departure(models.Model):
    date = models.DateField(verbose_name='дата выезда')
    departure_time = models.TimeField(verbose_name='время выезда')
    return_time = models.TimeField(verbose_name='время возвращения')
    place_of_work = models.CharField(max_length=40, verbose_name='место/цель выезда')
    distance = models.PositiveIntegerField(blank=True, null=True, verbose_name='пройдено (км)')
    with_pump = models.PositiveIntegerField(blank=True, null=True, verbose_name='с насосом (мин)')
    without_pump = models.PositiveIntegerField(blank=True, null=True, verbose_name='без насоса (мин)')
    refueled = models.PositiveIntegerField(blank=True, null=True, verbose_name='заправлено (л)')

    card = models.ForeignKey(Card, related_name='departures', on_delete=models.CASCADE, verbose_name='карточка')
    user = models.ForeignKey(get_user_model(), related_name='departures', on_delete=models.CASCADE,
                             verbose_name='пользователь')
    norm = models.ForeignKey(Norm, related_name="departures", on_delete=models.CASCADE, verbose_name='норма')

    def show_departure(self):
        res = f'{self.departure_time.strftime("%H:%M")}-{self.return_time.strftime("%H:%M")}, {self.place_of_work}'
        if self.distance:
            res += f', пройдено: {self.distance} км'
        if self.with_pump:
            res += f', с насосом: {self.with_pump} мин'
        if self.without_pump:
            res += f', без насоса: {self.without_pump} мин'
        if self.refueled:
            res += f', заправлено: {self.refueled} л'
        return res

    def __str__(self):
        return f'{self.date} - {self.place_of_work}'

    class Meta:
        ordering = ["-date", "-return_time"]

    def get_absolute_url(self):
        return reverse('departure_detail', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        self.departure_time = self.departure_time.replace(second=0)
        self.return_time = self.return_time.replace(second=0)
        super().save(*args, **kwargs)
