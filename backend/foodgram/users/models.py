from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role_choices(models.TextChoices):
        USER = 'user', _('Пользователь')
        ADMINISTRATOR = 'admin', _('Администратор')
    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        max_length=150,
        unique=True)
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150
    )
    email = models.EmailField(
        verbose_name='Почтовый адрес',
        blank=False,
        unique=True,
        max_length=254,
        null=False,
    )

    @property
    def is_user(self):
        return self.role == User.Role_choices.USER

    @property
    def is_admin(self):
        return self.role == User.Role_choices.ADMINISTRATOR

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email
