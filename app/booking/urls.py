from django.urls import path

from rest_framework.routers import DefaultRouter

from app.booking.views import SurchargeViesSet, UsageFeeViesSet, ChargeViesSet, FreightRateViesSet, \
    RateViesSet, WMCalculateView, QuoteViesSet, BookingViesSet, StatusViesSet, ShipmentDetailsViesSet, OperationViewSet


app_name = 'booking'

router = DefaultRouter()
router.register(r'surcharge', SurchargeViesSet, basename='surcharge')
router.register(r'usage-fee', UsageFeeViesSet, basename='usage_fee')
router.register(r'charge', ChargeViesSet, basename='charge')
router.register(r'freight-rate', FreightRateViesSet, basename='freight_rate')
router.register(r'rate', RateViesSet, basename='rate')
router.register(r'quote', QuoteViesSet, basename='quote')
router.register(r'booking', BookingViesSet, basename='booking')
router.register(r'status', StatusViesSet, basename='status')
router.register(r'shipment-details', ShipmentDetailsViesSet, basename='shipment_details')
router.register(r'operation', OperationViewSet, basename='operation')

urlpatterns = router.urls

urlpatterns += [
    path('calculate/', WMCalculateView.as_view()),
]
