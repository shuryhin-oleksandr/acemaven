from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token, refresh_jwt_token
from rest_framework.routers import DefaultRouter
from rest_auth.views import PasswordChangeView

from django.urls import path

from app.core.views import CompanyEditViewSet, SignUpRequestViewSet, SignUpCheckView, UserSignUpView, \
    UserViewSet, UserProfileView, BankAccountViewSet, SelectChoiceView, EmailNotificationSettingViewSet


app_name = 'core'


router = DefaultRouter()
router.register(r'company-sign-up', SignUpRequestViewSet, basename='company-sign-up')
router.register(r'company', CompanyEditViewSet, basename='company-edit')
router.register(r'user', UserViewSet, basename='user-create')
router.register(r'bank-account', BankAccountViewSet, basename='bank-account')
router.register(r'email-settings', EmailNotificationSettingViewSet, basename='email-settings')

urlpatterns = router.urls

urlpatterns += [
    path('sign-in/', obtain_jwt_token),
    path('verify-token/', verify_jwt_token),
    path('refresh-token/', refresh_jwt_token),
    path('signup-check/', SignUpCheckView.as_view()),
    path('signup/', UserSignUpView.as_view()),
    path('me/', UserProfileView.as_view()),
    path('choices/', SelectChoiceView.as_view()),
    path('password-change/', PasswordChangeView.as_view()),
]
