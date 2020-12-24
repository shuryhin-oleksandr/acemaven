from django.contrib import admin

from app.booking.models import Surcharge, AdditionalSurcharge, FreightRate, TrackStatus, Direction


@admin.register(AdditionalSurcharge)
class AdditionalSurchargeAdmin(admin.ModelAdmin):
    pass


@admin.register(Surcharge)
class SurchargeAdmin(admin.ModelAdmin):
    pass


@admin.register(FreightRate)
class FreightRateAdmin(admin.ModelAdmin):
    pass


@admin.register(TrackStatus)
class TrackStatusAdmin(admin.ModelAdmin):
    list_display = ('title', )


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('title', )
