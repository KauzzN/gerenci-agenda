from django.contrib import admin
from .models import Profile

# Register your models here.
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['public_slug', 'nome_negocio', 'updated_at']
    search_fields = ['public_slug']
