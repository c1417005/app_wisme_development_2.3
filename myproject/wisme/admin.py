from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Page, CustomUser

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    readonly_fields = ["id","created_at","update_at"]

admin.site.register(CustomUser, UserAdmin)