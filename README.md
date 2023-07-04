# Продуктовый помощник Foodgram

## Описание проекта:

Foodgram - это сервис, где пользователи могут публиковать свои рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать список продуктов, которые необходимы для приготовления одного или нескольких выбранных блюд.

## Технологии:
    Python 3.9
    Django 3
    Django REST framework
    PostgreSQL
    Docker

## Структура .env файла:
    POSTGRES_USER=django_user
    POSTGRES_PASSWORD=mysecretpassword
    POSTGRES_DB=foodgram
    DB_HOST=db
    DB_PORT=5432
    SECRET_KEY = 'django-insecure-o1l)ms^%a5b=jokdc)&r9gxh4y*)84q25jw+m0=rtn2)-v&3be'

## Как установить проект:
- Клонируйте репозиторий с проектом на свой компьютер:
    ```
    git clone git@github.com:Osolodkov1/foodgram-project-react.git
    ```
- В папке infra создайте файл .env
- Соберите и запустите контейнеры:
    ```
    docker-compose up
    ```
- Выполните миграции:
    ```
    docker-compose exec backend python manage.py makemigrations
    docker-compose exec backend python manage.py migrate
    ```
- Заполните БД:
    ```
    docker-compose exec backend python manage.py import_csv
    ```  
- Соберите статику:
    ```
    docker-compose exec backend python manage.py collectstatic --no-input
    ```

## Автор
### Артём Осолодков
### https://github.com/Osolodkov1