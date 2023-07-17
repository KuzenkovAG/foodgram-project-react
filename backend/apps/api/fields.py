import base64
import re

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

KEY_WORDS = ['data:image/', ';base64,']
REG_EX_BASE64 = r'data:image/[(png), (jpg)]+;base64,.+'


class Base64ImageField(serializers.ImageField):
    """Image field what convert base64 to image."""
    def to_internal_value(self, data):
        if not re.match(REG_EX_BASE64, data):
            raise ValidationError('Image base64 wrong format.')

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            try:
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name='temp.' + ext
                )
            except ValueError:
                raise ValidationError('Image base64 wrong format.')
        return data
