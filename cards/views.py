from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import F, Sum
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView

from cards.forms import CardAddForm
from cards.models import Card
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
    # success_url = reverse_lazy('card-list')
    success_url = "/"
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
