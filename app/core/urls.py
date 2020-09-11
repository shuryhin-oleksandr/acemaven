from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token, refresh_jwt_token
from rest_framework.routers import DefaultRouter

from django.conf.urls import url
from django.urls import path

from app.core.views import CompanyEditViewSet, SignUpRequestViewSet, SignUpCheckView, UserSignUpView, \
    UserViewSet, BankAccountViewSet, CompanyActivateView


app_name = 'projects'

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'company-sign-up', SignUpRequestViewSet, basename='company-sign-up')
router.register(r'company', CompanyEditViewSet, basename='company-edit')
router.register(r'user', UserViewSet, basename='user-create')
router.register(r'bank-account', BankAccountViewSet, basename='bank-account')

urlpatterns = router.urls

urlpatterns += [
    path('sign-in/', obtain_jwt_token),
    path('verify-token/', verify_jwt_token),
    path('refresh-token/', refresh_jwt_token),
    path('signup-check/', SignUpCheckView.as_view()),
    path('signup/', UserSignUpView.as_view()),
    path('company-activate', CompanyActivateView.as_view()),
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
