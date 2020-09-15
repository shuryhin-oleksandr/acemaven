from django.contrib import admin
from django.db import transaction
from django.forms import model_to_dict
from django.http import HttpResponseRedirect

from app.core.models import CustomUser, Company, BankAccount, Role, SignUpRequest, SignUpToken
from app.core.utils import master_account_processing
from app.handling.models import LocalFee


admin.site.register(SignUpToken)


class LocalFeeInline(admin.TabularInline):
    model = LocalFee
    extra = 0


class RoleInline(admin.TabularInline):
    model = Role
    extra = 0


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 0


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'company')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'company')


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'company')
    inlines = (
        RoleInline,
    )

    def company(self, obj):
        return obj.companies.first()


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_active')
    list_filter = ('name',)
    search_fields = ('name', 'type')
    inlines = (
        RoleInline,
        BankAccountInline,
        LocalFeeInline,
    )


@admin.register(SignUpRequest)
class SignUpRequestAdmin(admin.ModelAdmin):
    change_form_template = 'core/sign_up_request_changeform.html'
    list_display = ('name', 'type', 'phone', 'approved')

    def response_change(self, request, obj):
        if "_company_sign_up" in request.POST:
            try:
                with transaction.atomic():
                    company_info = model_to_dict(obj, exclude=['id', 'master_email', 'approved'])
                    company = Company.objects.create(**company_info)
                    master_account_processing(company, obj.master_email)
                    obj.approved = True
                    obj.save()
                self.message_user(request, "Company saved. Link to register master account was sent.")
            except Exception as error:
                self.message_user(request, f"Company with provided phone number already exists. "
                                           f"Additional info [{error}]")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)
