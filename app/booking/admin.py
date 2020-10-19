from django.contrib import admin

from app.booking.models import Surcharge, AdditionalSurcharge, FreightRate


@admin.register(AdditionalSurcharge)
class AdditionalSurchargeAdmin(admin.ModelAdmin):
    pass


@admin.register(Surcharge)
class SurchargeAdmin(admin.ModelAdmin):
    pass


@admin.register(FreightRate)
class FreightRateAdmin(admin.ModelAdmin):
    pass
