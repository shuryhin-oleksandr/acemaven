from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.forms import model_to_dict
from django.http import HttpResponseRedirect

from app.core.models import CustomUser, Company, BankAccount, Role, SignUpRequest, SignUpToken
from app.core.utils import master_account_processing
from app.handling.models import LocalFee


MASTER_ACCOUNT_FIELDS = ['email', 'first_name', 'last_name', 'master_phone', 'position', ]
EXCLUDE_FIELDS = ['id', 'approved', *MASTER_ACCOUNT_FIELDS]


class LocalFeeInline(admin.TabularInline):
    model = LocalFee
    extra = 0


class RoleInline(admin.TabularInline):
    model = Role
    extra = 0


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 0


@admin.register(SignUpToken)
class SignUpTokenAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'token',
    )


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        'bank_name',
        'company',
        'account_type',
        'is_default',
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'company',
    )


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'first_name',
        'last_name',
        'email',
        'company',
    )
    list_display_links = (
        'id',
        'first_name',
        'last_name',
        'email',
    )
    inlines = (
        RoleInline,
    )

    def company(self, obj):
        return obj.companies.first()


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'type',
        'phone',
    )
    list_filter = (
        'name',
    )
    search_fields = (
        'name',
        'type',
    )
    inlines = (
        RoleInline,
        BankAccountInline,
        LocalFeeInline,
    )


@admin.register(SignUpRequest)
class SignUpRequestAdmin(admin.ModelAdmin):
    change_form_template = 'core/sign_up_request_changeform.html'
    list_display = (
        'name',
        'type',
        'phone',
        'approved',
    )

    def response_change(self, request, obj):
        if "_company_sign_up" in request.POST:
            if obj.approved:
                self.message_user(request, "Sign up request was already approved.")
            else:
                try:
                    with transaction.atomic():
                        company_info = model_to_dict(obj, exclude=EXCLUDE_FIELDS)
                        company = Company.objects.create(**company_info)
                        master_account_info = {item if 'master_' not in item else item.replace('master_', ''): getattr(obj, item) for item in MASTER_ACCOUNT_FIELDS}
                        master_account_processing(company, master_account_info)
                        obj.approved = True
                        obj.save()
                    token = SignUpToken.objects.filter(user=get_user_model().objects.filter(email=obj.email).first()).first().token
                    self.message_user(request, "Company saved. Link to register master account was sent.")
                    self.message_user(request, f"Registration link - 192.168.1.33:8000/create-account?token={token}")
                    # TODO: Do not push test user message and token.
                except Exception as error:
                    self.message_user(request, f"Company with provided phone number or tax id already exists. "
                                               f"Additional info [{error}]")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)
