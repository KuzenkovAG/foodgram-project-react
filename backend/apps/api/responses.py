from typing import Callable, Dict, Union

from django.db.models import Model
from django.db.models.base import ModelBase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer


def get_response_for_create_or_delete(
            method: str,
            obj: Model,
            relation_model: ModelBase,
            action: str,
            data: Dict,
            serializer_class: Union[Callable, Serializer]
        ) -> Response:
    """Return response after create or delete relation."""
    relation = relation_model.objects.filter(**data)
    if method == 'POST':
        if relation.exists():
            errors = f'{obj} already in {action}.'
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        relation_model.objects.create(**data)
        serializer = serializer_class(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    if method == 'DELETE':
        if not relation.exists():
            errors = f'{obj} not in {action}.'
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        'Unsupported method',
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
