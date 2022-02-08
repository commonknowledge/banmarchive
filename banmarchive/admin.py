import imp
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from banmarchive import models


@admin.register(models.User)
class User(UserAdmin):
    pass
