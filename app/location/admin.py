from django.contrib import admin

from app.location.models import Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'currency', 'is_main', )
    search_fields = ('name', 'code', )
