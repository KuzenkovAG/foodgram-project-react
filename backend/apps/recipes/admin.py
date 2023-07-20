from django.contrib import admin
from django.utils.html import format_html

from . import models


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin for Ingredients model."""
    list_display = ('id', 'name', 'measurement_unit')


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for Tag model."""
    list_display = ('id', 'name', 'color', 'slug')
    list_filter = ('name',)


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin for Recipe model."""
    list_display = ('id', 'name', 'author')
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('in_favorites_count',)

    def in_favorites_count(self, obj):
        html_text = (
            '{}<br>'
            '<p class="help" style="padding-left: 0px; margin-left: 0px">'
            '{}'
            '</p>'
        )
        return format_html(
            html_text,
            obj.get_count_in_favorites(),
            "Количество добавлений в избранное.",
        )
