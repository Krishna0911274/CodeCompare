from django.contrib import admin
from .models import SavedCode

@admin.register(SavedCode)
class SavedCodeAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "language", "created_at")
    list_filter = ("language", "created_at")
    search_fields = ("title", "user__username")