from rest_framework.routers import DefaultRouter

from app.handling.views import CarrierViewSet, PortViewSet


app_name = 'handling'

router = DefaultRouter()
router.register(r'carrier', CarrierViewSet, basename='carrier')
router.register(r'port', PortViewSet, basename='port')

urlpatterns = router.urls
