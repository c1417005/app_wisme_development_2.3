from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Page, Chapter, CustomUser


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ["order", "title", "content"]
    ordering = ["order"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    readonly_fields = ["id","created_at","update_at"]
    inlines = [ChapterInline]


admin.site.register(CustomUser, UserAdmin)