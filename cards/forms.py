from datetime import timedelta
from datetime import datetime
from functools import reduce

from bootstrap_datepicker_plus.widgets import MonthPickerInput, DatePickerInput, TimePickerInput
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import QuerySet, F

from cards.models import Truck, Norm, Card, Departure


class CardAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.update = kwargs.pop("update", False)
        super().__init__(*args, **kwargs)

    month = forms.DateField(label="дата карты:",
                            widget=MonthPickerInput(attrs={'class': 'form-control'}))
    mileage = forms.IntegerField(label="пробег на 1 число месяца:",
                                 widget=forms.NumberInput(attrs={'class': 'form-control'}))
    remaining_fuel = forms.DecimalField(label='остаток топлива на 1 число месяца:',
                                        widget=forms.NumberInput(attrs={'class': 'form-control'}))
    truck = forms.ModelChoiceField(queryset=Truck.objects.all(),
                                   label='автомобиль:',
                                   widget=forms.Select(attrs={'class': 'form-control'}))
    norm = forms.ModelChoiceField(queryset=Norm.objects.all(),
                                  label='норма расхода топлива:',
                                  widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Card
        fields = ['month', 'mileage', 'remaining_fuel', 'truck', 'norm']

    def clean(self):
        cd = super().clean()
        month = cd.get('month')
        truck = cd.get('truck')

        # исключает перезапись карточки
        if self.update:
            if Card.objects.filter(month__month=month.month, truck=truck).exists() \
                    and self.instance.month.month != month.month \
                    or Card.objects.filter(month__month=month.month, truck=truck).exists() \
                    and self.instance.truck != truck:
                raise ValidationError('Такая карточка уже существует')
        else:
            if Card.objects.filter(month__month=month.month, truck=truck).exists():
                raise ValidationError('Такая карточка уже существует')


class DepartureAddForm(forms.ModelForm):
    date = forms.DateField(
        label='Дата выезда',
        widget=DatePickerInput(attrs={'class': 'form-control'}))
    current_mileage = forms.IntegerField(
        required=False,
        label='Тек. спидометр (км)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    # mileage_end = forms.IntegerField(
    #     required=False,
    #     label='Пробег после выезда (км)',
    #     widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        fields = ['date',
                  'departure_time', 'return_time',
                  'place_of_work', 'current_mileage',
                  'distance',
                  'with_pump', 'without_pump',
                  'refueled',
                  'card', 'user', 'norm'
                  ]
        model = Departure

        widgets = {
            'departure_time': TimePickerInput(attrs={'class': 'form-control'}),
            'return_time': TimePickerInput(attrs={'class': 'form-control'}),
            'place_of_work': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            # 'mileage_start': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'mileage_end': forms.NumberInput(attrs={'class': 'form-control'}),
            'with_pump': forms.NumberInput(attrs={'class': 'form-control'}),
            'without_pump': forms.NumberInput(attrs={'class': 'form-control'}),
            'refueled': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'fuel_consumption': forms.HiddenInput(),
            'card': forms.HiddenInput(),
            'user': forms.HiddenInput(),
            'norm': forms.HiddenInput()
        }

    def clean(self):
        cd: dict = super().clean()
        departures: QuerySet = self.initial['card'].departures.all()

        # отслеживает, чтобы не было пересекающихся по времени выездов
        cur_departure_time = datetime.combine(cd.get('date'), cd.get('departure_time'))
        cur_return_time = datetime.combine(cd.get('date'), cd.get('return_time'))
        for departure in departures:

            departure_time = datetime.combine(departure.date, departure.departure_time)
            return_time = datetime.combine(departure.date, departure.return_time)
            if departure_time < cur_departure_time < return_time or \
                    departure_time < cur_return_time < return_time or \
                    cur_departure_time <= departure_time and cur_return_time >= return_time:
                raise ValidationError("В это время уже записан выезд или время выезда и возвращения одинаковы")

        if not cd.get('distance') \
                and not cd.get('with_pump') \
                and not cd.get('without_pump'):
            self.add_error("with_pump", 'или это заполнить')
            self.add_error("without_pump", 'или это заполнить')
            self.add_error("distance", 'или это заполнить')
            raise ValidationError(
                'Одно из указанных полей должно быть заполнено')
        return cd


class DepartureUpdateForm(forms.ModelForm):

    def __init__(self, departure, *args, **kwargs):
        self.departure = departure
        super().__init__(*args, **kwargs)

    date = forms.DateField(
        label='Дата выезда',
        widget=DatePickerInput(attrs={'class': 'form-control'}))
    current_mileage = forms.IntegerField(
        required=False,
        label='Тек. спидометр (км)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    # mileage_end = forms.IntegerField(
    #     required=False,
    #     label='Пробег после выезда (км)',
    #     widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        fields = ['date',
                  'departure_time', 'return_time',
                  'place_of_work', 'current_mileage',
                  'distance',
                  'with_pump', 'without_pump',
                  'refueled',
                  'card', 'user', 'norm'
                  ]
        model = Departure

        widgets = {
            'departure_time': TimePickerInput(attrs={'class': 'form-control'}),
            'return_time': TimePickerInput(attrs={'class': 'form-control'}),
            'place_of_work': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            # 'mileage_start': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'mileage_end': forms.NumberInput(attrs={'class': 'form-control'}),
            'with_pump': forms.NumberInput(attrs={'class': 'form-control'}),
            'without_pump': forms.NumberInput(attrs={'class': 'form-control'}),
            'refueled': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'fuel_consumption': forms.HiddenInput(),
            'card': forms.HiddenInput(),
            'user': forms.HiddenInput(),
            'norm': forms.HiddenInput()
        }



    def clean(self):

        cd: dict = super().clean()
        departures: QuerySet = self.initial['card'].departures.exclude(id=self.departure.id)

        # отслеживает, чтобы не было пересекающихся по времени выездов
        cur_departure_time = datetime.combine(cd.get('date'), cd.get('departure_time'))
        cur_return_time = datetime.combine(cd.get('date'), cd.get('return_time'))
        for departure in departures:

            departure_time = datetime.combine(departure.date, departure.departure_time)
            return_time = datetime.combine(departure.date, departure.return_time)
            if departure_time < cur_departure_time < return_time or \
                    departure_time < cur_return_time < return_time or \
                    cur_departure_time <= departure_time and cur_return_time >= return_time:
                raise ValidationError("В это время уже записан выезд или время выезда и возвращения одинаковы")

        if not cd.get('distance') \
                and not cd.get('with_pump') \
                and not cd.get('without_pump'):
            self.add_error("with_pump", 'или это заполнить')
            self.add_error("without_pump", 'или это заполнить')
            self.add_error("distance", 'или это заполнить')
            raise ValidationError(
                'Одно из указанных полей должно быть заполнено')

        return cd
