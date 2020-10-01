from django.contrib import admin

from app.location.models import Country, Region, State, InternationalZone


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'currency',)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    pass


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    pass


@admin.register(InternationalZone)
class InternationalZoneAdmin(admin.ModelAdmin):
    pass
