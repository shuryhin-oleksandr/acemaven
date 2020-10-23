from rest_framework.routers import DefaultRouter

from app.handling.views import CarrierViewSet, PortViewSet, ShippingModeViewSet, ShippingTypeViewSet, CurrencyViewSet, \
    PackagingTypeViewSet


app_name = 'handling'

router = DefaultRouter()
router.register(r'carrier', CarrierViewSet, basename='carrier')
router.register(r'currency', CurrencyViewSet, basename='currency')
router.register(r'port', PortViewSet, basename='port')
router.register(r'shipping-mode', ShippingModeViewSet, basename='shipping_mode')
router.register(r'shipping-type', ShippingTypeViewSet, basename='shipping_type')
router.register(r'packaging-type', PackagingTypeViewSet, basename='packaging-type')


urlpatterns = router.urls
