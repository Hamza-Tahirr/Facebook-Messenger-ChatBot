from django.contrib import admin
from django.urls import re_path

from bot.views import index, web_hook

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^$', index, name="home"),
    re_path(r'^webhook', web_hook, name="webhook"),
]
