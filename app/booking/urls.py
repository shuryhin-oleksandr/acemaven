from rest_framework.routers import DefaultRouter

from django.urls import path

from app.booking.views import SurchargeViesSet, UsageFeeViesSet, ChargeViesSet, CheckDateView


app_name = 'booking'

router = DefaultRouter()
router.register(r'surcharge', SurchargeViesSet, basename='surcharge')
router.register(r'usage-fee', UsageFeeViesSet, basename='usage_fee')
router.register(r'charge', ChargeViesSet, basename='charge')

urlpatterns = router.urls

urlpatterns += [
    path('check-date/', CheckDateView.as_view()),
]
