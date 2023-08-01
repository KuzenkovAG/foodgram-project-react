# Foodgram
Сервис для рецептов

### Деплой
https://foodgram-alexeyk.ddns.net/

username - admin
password - admin


## Технологии
#### Backend
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
#### Frontend
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
#### Infrastructure
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)

## Поддерживаемые функции
- Просмотр рецептов;
- Создание/редактирование рецептов;
- Подписка на авторов;
- Добавление рецепта в избранное;
- Добавление рецепта в корзину;
- Скачивание списка ингредиентов (для рецептов, находящихся в корзине).

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
