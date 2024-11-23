import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


def user_directory_path(instance, filename):
    # todo исправить ошибку при регистрации  нет user = get_user_model().objects.get(pk=instance.pk)
    # user = get_user_model().objects.get(pk=instance.pk)
    # if user.photo:
    #     if os.path.exists(user.photo.path):
    #         os.remove(user.photo.path)
    imgname = f'users/{instance.username}/{filename}'
    return imgname


class User(AbstractUser):
    photo = models.ImageField(upload_to=user_directory_path, blank=True, null=True, verbose_name='Фотография')
    date_birth = models.DateField(blank=True, null=True, verbose_name='Дата рождения')



