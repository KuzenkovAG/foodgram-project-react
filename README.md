# Foodgram
Сервис для рецептов

## Поддерживаемые функции
- Просмотр рецептов;
- Добавление в избранное;
- Добавление в корзину;
- Подписка на авторов;
- Создание/редактирование рецептов;
- Скачивание списка ингредиентов для рецептов, находящихся в корзине.

## Tech
- Python
- Django
- DRF
- React
- Nginx
- Postgres

## Запуск через Docker-Compose (Windows)
Клонируйте репозиторий
```sh
git clone git@github.com:KuzenkovAG/foodgram-project-react.git
```
Перейдите в каталог
```sh
cd infra/
```
Запуск в контейнере Docker
```sh
docker compose up
```
Применение миграций
```sh
docker compose exec backend python manage.py migrate
```
Добавление ингредиентов в базу
```sh
docker compose exec backend python manage.py add_ingredients
```
Сервис станет доступен по адресу
```sh
http://localhost/
```


## Автор
[Alexey Kuzenkov]


   [Alexey Kuzenkov]: <https://github.com/KuzenkovAG>
