from django.urls import path

from rest_framework.routers import DefaultRouter

from app.booking.views import SurchargeViesSet, UsageFeeViesSet, ChargeViesSet, FreightRateViesSet, \
    RateViesSet, WMCalculateView


app_name = 'booking'

router = DefaultRouter()
router.register(r'surcharge', SurchargeViesSet, basename='surcharge')
router.register(r'usage-fee', UsageFeeViesSet, basename='usage_fee')
router.register(r'charge', ChargeViesSet, basename='charge')
router.register(r'freight-rate', FreightRateViesSet, basename='freight_rate')
router.register(r'rate', RateViesSet, basename='rate')

urlpatterns = router.urls

urlpatterns += [
    path('calculate/', WMCalculateView.as_view()),
]
