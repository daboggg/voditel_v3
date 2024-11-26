from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView, LogoutView, PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from mixins import ErrorMessageMixin
from users.forms import LoginUserForm, RegisterUserForm, ProfileUserForm, UserPasswordChangeForm, UserPasswordResetForm


class LoginUser(SuccessMessageMixin, ErrorMessageMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}
    success_message = "%(username)s - успешный вход"
    # success_message = "%(calculated_field)s - успешный вход"
    error_message = "Ошибка!"


class LogoutUser(LogoutView):
    def post(self, request, *args, **kwargs):
        messages.warning(request, f'{request.user} - вышел из приложения')
        return super().post(request, *args, **kwargs)


class RegisterUser(SuccessMessageMixin, ErrorMessageMixin, CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': 'Регистрация'}
    success_url = reverse_lazy('users:login')
    success_message = "%(username)s - успешная регистрация"
    error_message = "Ошибка!"


class ProfileUser(SuccessMessageMixin, ErrorMessageMixin, LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {'title': 'Профиль пользователя'}
    success_message = "%(username)s - профиль изменен"
    error_message = "Ошибка!"

    def get_success_url(self):
        return reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user


class UserPasswordChange(SuccessMessageMixin, ErrorMessageMixin, PasswordChangeView):
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:password_change_done")
    template_name = "users/password_change_form.html"
    extra_context = {"title": "Изменение пароля"}
    success_message = "пароль изменен"
    error_message = "Ошибка!"


class UserPasswordReset(PasswordResetView):
    form_class = UserPasswordResetForm
