from datetime import date, datetime
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import F, Sum, QuerySet
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, FormView
from weasyprint import HTML, CSS

from cards.forms import CardAddForm, DepartureAddForm, ReportEmailForm, ReportChoiceForm
from cards.models import Card, Departure, Norm
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
    res: dict = card.departures. \
        annotate(mileage_consumption=F('distance') * F('norm__liter_per_km'),
                 with_pump_consumption=F('with_pump') * F('norm__work_with_pump_liter_per_min'),
                 without_pump_consumption=F('without_pump') * F('norm__work_without_pump_liter_per_min')). \
        aggregate(
            total_distance=Sum('distance', default=0),
            total_mileage_consumption=Sum('mileage_consumption', default=0),
            total_time_with_pump=Sum('with_pump', default=0),
            total_with_pump_consumption=Sum('with_pump_consumption', default=0),
            total_time_without_pump=Sum('without_pump', default=0),
            total_without_pump_consumption=Sum('without_pump_consumption', default=0),
            total_refueled=Sum('refueled', default=0),
            total_fuel_consumption=F('total_mileage_consumption') + F('total_with_pump_consumption') + F(
                'total_without_pump_consumption'),
            remaining_fuel=card.remaining_fuel + F('total_refueled') - F('total_fuel_consumption'),
            current_mileage=card.mileage + F('total_distance'))

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

    def get_success_url(self):
        return reverse_lazy('card_detail', kwargs={'pk': self.object.pk})

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
            fuel_consumption += self.object.distance * self.object.norm.liter_per_km
        if self.object.with_pump:
            fuel_consumption += self.object.with_pump * self.object.norm.work_with_pump_liter_per_min
        if self.object.without_pump:
            fuel_consumption += self.object.without_pump * self.object.norm.work_without_pump_liter_per_min

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
    form_class = DepartureAddForm
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
        kwargs['update'] = True
        return kwargs


class NormList(LoginRequiredMixin, ListView):
    model = Norm
    template_name = "cards/norm_list.html"
    extra_context = {'title': 'Нормы'}
    context_object_name = 'norms'


class NormAdd(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin, CreateView):
    model = Norm
    template_name = 'cards/norm_add.html'
    extra_context = {'title': 'Добавить норму'}
    success_url = reverse_lazy('norm_list')
    success_message = "Норма создана"
    error_message = 'Ошибка!'
    fields = '__all__'


class NormDelete(LoginRequiredMixin, DeleteView):
    model = Norm
    success_url = reverse_lazy('norm_list')


class NormUpdate(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin, UpdateView):
    model = Norm
    fields = '__all__'
    success_url = reverse_lazy('norm_list')
    success_message = "Данные изменены"
    error_message = "Ошибка!"
    template_name = 'cards/norm_add.html'
    extra_context = {'title': 'Изменить норму'}


class ReportDetail(LoginRequiredMixin, DetailView):
    model = Card
    template_name = 'cards/report_detail.html'
    context_object_name = 'report'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Отчет {self.object}'

        report_data = calculated_result(self.object)
        ctx['report_data'] = report_data
        return ctx


def convert_html_to_pdf_stream(template: str, context: dict) -> BytesIO:
    html_content = render_to_string(template, context)
    memory_buffer = BytesIO()
    pdf = HTML(string=html_content).write_pdf(target=memory_buffer, stylesheets=[CSS(string='@page {size: landscape}')])

    return memory_buffer


class FullReport(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        card = Card.objects.get(pk=kwargs.get('pk'))

        report_data = calculated_result(card)
        report_data['card'] = card

        pdf_stream = convert_html_to_pdf_stream('cards/full_report_pdf.html', report_data)
        response = HttpResponse(pdf_stream.getvalue(), content_type='application/pdf')
        return response


class ShortReport(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        card = Card.objects.get(pk=kwargs.get('pk'))

        report_data = calculated_result(card)
        report_data['card'] = card

        pdf_stream = convert_html_to_pdf_stream('cards/short_report_pdf.html', report_data)
        response = HttpResponse(pdf_stream.getvalue(), content_type='application/pdf')
        return response


class FullReportEmail(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin, FormView):
    template_name = 'cards/report_email.html'
    success_message = "Email отправлен"
    error_message = 'Ошибка!'
    form_class = ReportEmailForm
    extra_context = {'title': 'Полный отчет на email'}

    def get_success_url(self):
        return reverse_lazy('card_detail', kwargs={'pk': self.kwargs.get('pk')})

    def setup(self, request, *args, **kwargs):
        self.card = get_object_or_404(Card, pk=kwargs['pk'])
        report_data = calculated_result(self.card)
        report_data['card'] = self.card
        self.pdf_stream = convert_html_to_pdf_stream('cards/full_report_pdf.html', report_data)
        super().setup(request, *args, **kwargs)

    def form_valid(self, form):
        email = EmailMessage(
            subject=f'Отчет {self.card}',
            body='Отчет находится в прикрепленном файле',
            from_email='zvovan77@yandex.ru',
            to=[form.cleaned_data.get("email")]
        )
        email.attach(f"отчет-{self.card.truck.name}-{self.card.month.month}-{self.card.month.year}.pdf", self.pdf_stream.getvalue())
        email.send()
        return super().form_valid(form)


class ShortReportEmail(LoginRequiredMixin, SuccessMessageMixin, ErrorMessageMixin, FormView):
    template_name = 'cards/report_email.html'
    success_message = "Email отправлен"
    error_message = 'Ошибка!'
    form_class = ReportEmailForm
    extra_context = {'title': 'Короткий отчет на email'}

    def get_success_url(self):
        return reverse_lazy('card_detail', kwargs={'pk': self.kwargs.get('pk')})

    def setup(self, request, *args, **kwargs):
        self.card = get_object_or_404(Card, pk=kwargs['pk'])
        report_data = calculated_result(self.card)
        report_data['card'] = self.card
        self.pdf_stream = convert_html_to_pdf_stream('cards/short_report_pdf.html', report_data)
        super().setup(request, *args, **kwargs)

    def form_valid(self, form):
        email = EmailMessage(
            subject=f'Отчет {self.card}',
            body='Отчет находится в прикрепленном файле',
            from_email='zvovan77@yandex.ru',
            to=[form.cleaned_data.get("email")]
        )
        email.attach(f"отчет-{self.card.truck.name}-{self.card.month.month}-{self.card.month.year}.pdf", self.pdf_stream.getvalue())
        email.send()
        return super().form_valid(form)


class ReportChoice(LoginRequiredMixin, FormView):
    template_name = 'cards/report_choice.html'
    form_class = ReportChoiceForm
    extra_context = {'title': 'Выбор периода'}

    def __init__(self, *args, **kwargs):
        self.card = None
        self.cards = None
        super().__init__(*args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['month'] = date.today().month
        initial['year'] = date.today().year
        return initial

    def form_valid(self, form):
        cd = form.cleaned_data
        cards = Card.objects.filter(month__year=cd.get('year'), month__month=cd.get('month'))
        if not cards:
            messages.warning(self.request, 'Нет карточек за этот период')
            return redirect(reverse_lazy('report_choice'))
        elif len(cards) == 1:
            self.card = cards[0]
            report_data = calculated_result(cards[0])
            report_data['card'] = cards[0]
            pdf_stream = convert_html_to_pdf_stream('cards/short_report_pdf.html', report_data)
        else:
            self.cards = cards
            reports_data = list()
            for card in cards:
                report_data = calculated_result(card)
                report_data['card'] = card
                reports_data.append(report_data)
            pdf_stream = convert_html_to_pdf_stream('cards/short_reports_pdf.html', {'data': reports_data})

        # если есть значение в поле email отправляем письмо по введенному адресу
        if cd.get('email'):
            email = EmailMessage(
                body='Отчет находится в прикрепленном файле',
                from_email='zvovan77@yandex.ru',
                to=[cd.get("email")]
            )
            if self.card:
                email.subject = f'Отчет {self.card}'
                email.attach(f"отчет-{self.card.truck.name}-{self.card.month.month}-{self.card.month.year}.pdf",
                             pdf_stream.getvalue())
            elif self.cards:
                email.subject = f'Отчет {self.cards[0].truck.name} и {self.cards[1]}'
                email.attach(f"отчет-{self.cards[0].truck.name}-{self.cards[1].truck.name}-{self.cards[0].month.month}-{self.cards[0].month.year}.pdf",
                             pdf_stream.getvalue())

            email.send()

        response = HttpResponse(pdf_stream.getvalue(), content_type='application/pdf')
        return response
