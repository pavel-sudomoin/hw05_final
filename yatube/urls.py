"""yatube URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.flatpages import views
from django.conf.urls import handler404, handler500

handler404 = "posts.views.page_not_found"
handler500 = "posts.views.server_error"

urlpatterns = [
    #  обработчик для главной страницы ищем в urls.py приложения posts
    path("", include("posts.urls")),

    #  регистрация и авторизация
    path("auth/", include("users.urls")),

    #  если нужного шаблона для /auth не нашлось в файле users.urls — 
    #  ищем совпадения в файле django.contrib.auth.urls
    path("auth/", include("django.contrib.auth.urls")),

    #  раздел администратора
    path("admin/", admin.site.urls),

    # flatpages
    path("about/", include("django.contrib.flatpages.urls")),
    path("about-author/", views.flatpage, {"url": "/about-author/"}, name="author"),
    path("about-spec/", views.flatpage, {"url": "/about-spec/"}, name="spec"),
]
