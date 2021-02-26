from tabbed_admin import TabbedModelAdmin

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.forms import model_to_dict
from django.http import HttpResponseRedirect

from app.core.models import CustomUser, Company, BankAccount, Role, SignUpRequest, SignUpToken, Review

from app.handling.models import LocalFee
from app.core.tasks import create_company_empty_fees


MASTER_ACCOUNT_FIELDS = ['email', 'first_name', 'last_name', 'master_phone', 'position', ]
EXCLUDE_FIELDS = ['id', 'approved', *MASTER_ACCOUNT_FIELDS]


class LocalFeeInline(admin.TabularInline):
    template = 'core/local_fee_inline_tabular.html'
    fields = ('shipping_mode', 'value_type', 'value', 'is_active', )
    readonly_fields = ('shipping_mode', )
    radio_fields = {'value_type': admin.VERTICAL}
    model = LocalFee
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False

    def get_queryset(self, request):
        fee_type = request.GET.get('fee_type', 'booking')
        queryset = super().get_queryset(request)
        if not self.has_view_or_change_permission(request):
            queryset = queryset.none()
        return queryset.filter(fee_type=fee_type)


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
        'is_default',
    )
    fieldsets = (
        (None, {
            'fields': (
                'bank_name',
                'bank_number',
                'branch',
                'number',
                'pix_key',
                'is_default',
            ),
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(company__isnull=True, is_platforms=True)

    def save_model(self, request, obj, form, change):
        obj.is_platforms = True
        obj.save()


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
        return obj.get_company()


@admin.register(Company)
class CompanyAdmin(TabbedModelAdmin):
    model = Company
    list_display = (
        'id',
        'name',
        'type',
        'date_created',
    )
    list_display_links = (
        'id',
        'name',
    )
    tab_company = (
        (None, {
            'fields': (
                'type',
                'name',
                (
                    'address_line_first',
                    'address_line_second',
                ),
                'state',
                'city',
                'zip_code',
                'phone',
                'tax_id',
                (
                    'employees_number',
                    'website',
                ),
            ),
        }),
        RoleInline,
    )

    tab_fee = (
        LocalFeeInline,
    )

    tabs = (
        ('Company', tab_company),
        ('Fees', tab_fee),
    )

    search_fields = ('id', 'name',)


@admin.register(SignUpRequest)
class SignUpRequestAdmin(admin.ModelAdmin):
    change_form_template = 'core/sign_up_request_changeform.html'
    list_display = (
        'name',
        'type',
        'phone',
        'approved',
    )
    fieldsets = (
        ('Company info', {
            'fields': (
                'type',
                'name',
                'address_line_first',
                'address_line_second',
                'state',
                'city',
                'zip_code',
                'phone',
                'tax_id',
                (
                    'employees_number',
                    'website',
                ),
                'approved',
            ),
        }),
        ('Contact person info', {
            'fields': (
                'email',
                'first_name',
                'last_name',
                'master_phone',
                'position',
            ),
        }),
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
                        master_account_info = {'email': obj.email}
                        master_account_processing(company, master_account_info)
                        obj.approved = True
                        obj.save()
                        transaction.on_commit(lambda: create_company_empty_fees.delay(company.id))
                    token = SignUpToken.objects.filter(user=get_user_model().objects.filter(email=obj.email).first()).first().token
                    self.message_user(request, "Company saved. Link to register master account was sent.")
                    self.message_user(request, f"Registration link - 192.168.1.33:8000/create-account?token={token}")
                    # TODO: Do not push test user message and token.
                except Exception as error:
                    self.message_user(request, f"Company with provided phone number or tax id already exists. "
                                               f"Additional info [{error}]")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    change_form_template = 'core/review_changeform.html'
    list_display = (
        'operation',
        'rating',
        'comment',
        'date_created',
        'approved',
    )
    ordering = (
        'approved',
        'date_created',
    )
    fieldsets = (
        ('Review info', {
            'fields': (
                'rating',
                'comment',
                'reviewer',
                'operation',
            ),
        }),
        ('Approved', {
            'fields': (
                'approved',
            ),
        }),
    )

    def response_change(self, request, obj):
        if "_approve_review" in request.POST:
            if obj.approved:
                self.message_user(request, "Review was already approved.")
            else:
                obj.approved = True
                obj.save()
                self.message_user(request, "Review successfully approved.")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)
