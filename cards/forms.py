from bootstrap_datepicker_plus.widgets import MonthPickerInput
from django import forms
from django.core.exceptions import ValidationError

from cards.models import Truck, Norm, Card


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

