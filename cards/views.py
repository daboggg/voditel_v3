from datetime import date, datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import F, Sum, QuerySet
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView

from cards.forms import CardAddForm, DepartureAddForm, DepartureUpdateForm
from cards.models import Card, Departure
from mixins import ErrorMessageMixin


def home(request):
    return render(request, 'cards/home.html', {'title': 'Главная страница'})


class CardList(LoginRequiredMixin, ListView):
    model = Card
    template_name = "cards/card_list.html"
    extra_context = {'title': 'Список карточек'}
    context_object_name = 'cards'
    paginate_by = 7


class CardAdd(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin, CreateView):
    form_class = CardAddForm
    template_name = 'cards/card_add.html'
    extra_context = {'title': 'Добавить карточку'}
    success_message = "Карточка создана"
    error_message = 'Ошибка!'

    def get_initial(self):
        initial = super().get_initial()
        initial['month'] = date(date.today().year, date.today().month, 1)
        return initial


def calculated_result(card: Card) -> dict:
    res = card.departures.aggregate(
        total_distance=Sum('distance', default=0),
        total_mileage_consumption=Sum('distance', default=0) * card.norm.liter_per_km,
        total_time_with_pump=Sum('with_pump', default=0),
        total_with_pump_consumption=Sum('with_pump', default=0) * card.norm.work_with_pump_liter_per_min,
        total_time_without_pump=Sum('without_pump', default=0),
        total_without_pump_consumption=Sum('without_pump',
                                           default=0) * card.norm.work_without_pump_liter_per_min,
        total_refueled=Sum('refueled', default=0),
        total_fuel_consumption=F('total_mileage_consumption') + F('total_with_pump_consumption') + F(
            'total_without_pump_consumption'),
        remaining_fuel=card.remaining_fuel + F('total_refueled') - F('total_fuel_consumption'),
        current_mileage=card.mileage + F('total_distance')
    )
    return res


class CardDetail(LoginRequiredMixin, DetailView):
    model = Card
    template_name = 'cards/card_detail.html'
    context_object_name = 'card'

    def get_context_data(self, **kwargs):
        ctx: dict = super().get_context_data(**kwargs)
        ctx['title'] = f'{self.object}'

        # добавил в контекст вычисленные данные
        ctx.update(calculated_result(self.object))

        # для пагинации выездов
        res = dict()
        for item in self.object.departures.all():
            if item.date not in res:
                res[item.date] = []
            res.get(item.date).append(item)
        paginator = Paginator(list(res.values()), 7)
        page_obj = paginator.page(int(self.request.GET.get('page', 1)))
        ctx['paginator'] = paginator
        ctx['page_obj'] = page_obj
        ctx['departures'] = page_obj.object_list

        return ctx


class CardUpdate(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin, UpdateView):
    model = Card
    form_class = CardAddForm
    success_message = "Данные изменены"
    success_url = '/'
    error_message = "Ошибка!"
    template_name = 'cards/card_add.html'
    extra_context = {'title': 'Изменить карточку'}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['update'] = True
        return kwargs


class CardDelete(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Card
    success_url = reverse_lazy("card_list")
    success_message = "Карточка удалена"


class DepartureAdd(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin, CreateView):
    form_class = DepartureAddForm
    template_name = 'cards/departure_add.html'
    success_message = "Выезд добавлен"
    error_message = 'Ошибка!'

    def get_success_url(self):
        return reverse_lazy('card_detail', kwargs={'pk': self.card.id})

    def setup(self, request, *args, **kwargs):
        self.card = get_object_or_404(Card, pk=kwargs['pk'])
        super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Добавить выезд'
        ctx['card'] = self.card
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial['date'] = date.today()
        initial['current_mileage'] = calculated_result(self.card).get('current_mileage')
        initial['card'] = self.card
        initial['user'] = self.request.user
        initial['norm'] = self.card.norm

        # заполнить форму если ЕТО
        if 'eto' in self.request.GET:
            initial['departure_time'] = '08:00:00'
            initial['return_time'] = '08:30:00'
            initial['place_of_work'] = 'ЕТО'
            initial['without_pump'] = 5

        # заполнить форму если целевой дозор
        if 'dozor' in self.request.GET:
            initial['departure_time'] = '21:00:00'
            initial['return_time'] = '22:00:00'
            initial['place_of_work'] = 'Целевой дозор'
            initial['distance'] = 4
            initial['without_pump'] = 30

        return initial


class DepartureDetail(LoginRequiredMixin, DetailView):
    model = Departure
    template_name = 'cards/departure_detail.html'
    context_object_name = 'departure'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # все выезды в данной карточке
        departures: QuerySet = self.object.card.departures.all()

        # все выезды завершенные до данного выезда
        departures_before = list(filter(
            lambda a: datetime.combine(a.date, a.return_time) <
                      datetime.combine(self.object.date, self.object.return_time),
            departures))
        # общий пробег всех выездов до данного выезда
        total_distance = 0
        if departures_before:
            for departure in departures_before:
                if departure.distance:
                    total_distance += departure.distance

        print(departures_before)
        print(total_distance)

        # пробег до выезда
        mileage_start = self.object.card.mileage + total_distance

        # пробег после выезда
        if self.object.distance:
            mileage_end = mileage_start + self.object.distance
        else:
            mileage_end = mileage_start

        # топливо израсходовано за выезд
        fuel_consumption = 0
        if self.object.distance:
            fuel_consumption += self.object.distance * self.object.card.norm.liter_per_km
        if self.object.with_pump:
            fuel_consumption += self.object.with_pump * self.object.card.norm.work_with_pump_liter_per_min
        if self.object.without_pump:
            fuel_consumption += self.object.without_pump * self.object.card.norm.work_without_pump_liter_per_min

        ctx['mileage_start'] = mileage_start
        ctx['mileage_end'] = mileage_end
        ctx['fuel_consumption'] = fuel_consumption
        return ctx


class DepartureDelete(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Departure
    success_message = "Выезд удален"

    def get_success_url(self):
        return reverse_lazy("card_detail", kwargs={'pk': self.object.card.pk})


class DepartureUpdate(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin, UpdateView):
    model = Departure
    form_class = DepartureUpdateForm
    success_message = "Данные изменены"
    error_message = "Ошибка!"
    template_name = 'cards/departure_add.html'
    extra_context = {'title': 'Изменить данные'}

    def get_initial(self):
        initial = super().get_initial()
        initial['current_mileage'] = calculated_result(self.object.card).get('current_mileage')
        initial['user'] = self.request.user
        initial['card'] = self.object.card
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['departure'] = self.object
        return kwargs
