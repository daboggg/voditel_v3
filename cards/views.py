from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
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


class CardDetail(LoginRequiredMixin, DetailView):
    model = Card
    template_name = 'cards/card_detail.html'
    context_object_name = 'card'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'{self.object}'

        # актуальный остаток топлива в баках
        fuel_in_tanks = self.object.departures.aggregate(
            fuel_in_tanks=F('card__remaining_fuel') -
                          Sum('fuel_consumption') +
                          Sum('refueled', default=0)) \
            .get('fuel_in_tanks')
        ctx['fuel_in_tanks'] = fuel_in_tanks.normalize() if fuel_in_tanks else self.object.remaining_fuel

        # актуальное показание спидометра
        actual_mileage = self.object.departures.aggregate(
            actual_mileage=Sum('distance', default=0) + self.object.mileage
        ).get('actual_mileage')
        ctx['actual_mileage'] = actual_mileage

        # для пагинации выездов
        # res = dict()
        # for item in self.object.departures.all():
        #     if item.date not in res:
        #         res[item.date] = []
        #     res.get(item.date).append(item)
        # paginator = Paginator(list(res.values()), 7)
        # page_obj = paginator.page(int(self.request.GET.get('page', 1)))
        # ctx['paginator'] = paginator
        # ctx['page_obj'] = page_obj
        # ctx['departures'] = page_obj.object_list

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
