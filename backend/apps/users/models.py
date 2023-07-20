from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """User model."""
    block = models.BooleanField(
        'Блокировка пользователя',
        blank=True,
        null=True,
        default=False,
        help_text='Заблокированные пользователи не могут использовать сайт.'
    )

    @property
    def is_blocked(self):
        return self.block
