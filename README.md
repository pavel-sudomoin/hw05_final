# Спринт 6 для Yandex.Praktikum - Проект «Yatube»

## Описание проекта

Проект Yatube - это социальная сеть для публикации личных дневников.

Проект позволяет:

* регистрироваться и логиниться
* восстанавливать пароль по почте
* создавать личную страницу для публикации записей
* создавать и редактировать свои записи
* просматривать страницы других авторов
* комментировать записи других авторов
* подписываться на авторов
* группировать записи можно отправлять в определённую группу

Модерация записей, работа с пользователями, создание групп - осуществляется через встроенную панель администратора

В проекте реализовано автоматическое тестирование с помощью библиотеки `Unittest`, настроено кэширование.

Приложение разработано в учебных целях для **Yandex.Praktikum**.

## Используемые технологии

* Django 2.2
* Python 3.8
* Django HTML Templates
* Django Unittest
* SQLite

## Установка проекта

Клонируйте данный репозиторий на свой компьютер и перейдите в папку проекта.
<pre><code>git clone https://github.com/pavel-sudomoin/hw05_final</code>
<code>cd hw05_final</code></pre>

Создайте и активируйте виртуальное окружение:

<pre><code>python -m venv venv</code>
<code>source ./venv/Scripts/activate  #для Windows</code>
<code>source ./venv/bin/activate      #для Linux и macOS</code></pre>

Установите требуемые зависимости:

<pre><code>pip install -r requirements.txt</code></pre>

Примените миграции:

<pre><code>python manage.py migrate</code></pre>

Загрузите архив с необходимой статикой и распакуйте его в папку `posts/static`

<https://code.s3.yandex.net/backend-developer/learning-materials/static.zip>

Запустите django-сервер:

<pre><code>python manage.py runserver</code></pre>

Приложение будет доступно по адресу: <http://127.0.0.1:8000/>

## Работа с проектом

### Создание суперпользователя

<pre><code>python manage.py createsuperuser</code></pre>

## Авторы

* [Yandex.Praktikum](https://praktikum.yandex.ru/)

* [Судомоин Павел](https://github.com/pavel-sudomoin/)
