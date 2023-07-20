import csv

from django.core.management.base import BaseCommand

from ... import models


class Command(BaseCommand):
    help = "Import ingredients in db."

    def handle(self, *args, **options):
        path = 'static/data_csv/ingredients.csv'

        ingredients = models.Ingredient.objects.all()
        ingredients.delete()
        objects = []
        with open(path, encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                object = models.Ingredient(
                    name=row[0],
                    measurement_unit=row[1]
                )
                objects.append(object)

            created_objects = models.Ingredient.objects.bulk_create(objects)
            created_count = len(created_objects)
            self.stdout.write(
                self.style.SUCCESS(
                    f'(Добавлено ингредиентов: {created_count}'
                )
            )
