from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from tabbed_admin import TabbedModelAdmin

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction, models
from django.forms import model_to_dict, Textarea
from django.http import HttpResponseRedirect

from app.core.models import CustomUser, Company, BankAccount, Role, SignUpRequest, SignUpToken, Review

from app.handling.models import LocalFee, PixApiSetting
from app.core.tasks import create_company_empty_fees
from app.core.utils import master_account_processing

from django.utils.translation import ugettext_lazy as _

MASTER_ACCOUNT_FIELDS = ['email', 'first_name', 'last_name', 'master_phone', 'position', ]
EXCLUDE_FIELDS = ['id', 'approved', *MASTER_ACCOUNT_FIELDS]


class LocalFeeInline(admin.TabularInline):
    template = 'core/local_fee_inline_tabular.html'
    fields = ('shipping_mode', 'value_type', 'value', 'is_active',)
    readonly_fields = ('shipping_mode',)
    radio_fields = {'value_type': admin.VERTICAL}
    model = LocalFee
    extra = 0

    def formfield_for_choice_field(self, db_field, request, **kwargs):

        if db_field.name == "value_type":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in LocalFee.VALUE_TYPE_CHOICES]

        return super(LocalFeeInline, self).formfield_for_choice_field(db_field, request, **kwargs)

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

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups":
            kwargs["queryset"] = Group.objects.filter(name__in=['master', 'billing', 'support', ])
        return super(RoleInline, self).formfield_for_manytomany(db_field, request, **kwargs)


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 0


class PixApiSettingInline(admin.StackedInline):
    model = PixApiSetting
    extra = 0


@admin.register(SignUpToken)
class SignUpTokenAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'token',
    )


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    readonly_fields = ('bank_name',
                       'bank_number',
                       'branch',
                       'number',
                       'pix_key',)
    list_display = (
        'bank_name',
        'is_default',
    )
    inlines = [PixApiSettingInline, ]
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
        if hasattr(BankAccount.objects.first(), 'pix_api'):
            PixApiSetting.objects.create(
                bank_account_id=obj.id,
            )

    def get_readonly_fields(self, request, obj=None):
        if 'add' in request.META['PATH_INFO']:
            return ()
        else:
            return self.readonly_fields


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'company',
    )


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    readonly_fields = ('date_joined', 'last_login',)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols': 50})},
    }
    ordering = ('email',)
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

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
         ),
    )

    fieldsets = (
        (_('User info'), {
            'fields': (
                'email',
                'password',
                'first_name',
                'last_name',
                'language',
                'groups',
            ),
        }),
    )

    def company(self, obj):
        return obj.get_company()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups":
            kwargs["queryset"] = Group.objects.filter(name__in=['master', 'billing', 'support', ])
        return super(CustomUserAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    company.short_description = _("Company")


@admin.register(Company)
class CompanyAdmin(TabbedModelAdmin):
    model = Company
    list_display = (
        'id',
        'name',
        'type_choice',
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

    def get_queryset(self, request):
        return super().get_queryset(request)

    def type_choice(self, obj):
        choice = \
            next(filter(lambda x: x[0] == obj.type, Company.COMPANY_TYPE_CHOICES), Company.COMPANY_TYPE_CHOICES[0])[1]
        return _(choice)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "type":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in Company.COMPANY_TYPE_CHOICES]

        return super(CompanyAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    type_choice.short_description = _('Company Type')

    tabs = (
        (_('Company'), tab_company),
        (_('Fees'), tab_fee),
    )

    search_fields = ('id', 'name',)


@admin.register(SignUpRequest)
class SignUpRequestAdmin(admin.ModelAdmin):
    readonly_fields = ['type', 'name', 'address_line_first', 'address_line_second', 'state', 'city', 'zip_code',
                       'phone', 'tax_id', 'employees_number', 'website', 'email', 'first_name', 'last_name',
                       'master_phone', 'position', 'approved']
    change_form_template = 'core/sign_up_request_changeform.html'
    list_display = (
        'name',
        'type_choice',
        'phone',
        'approved',
    )
    fieldsets = (
        (_('Company info'), {
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
        (_('Contact person info'), {
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
                self.message_user(request, _("Sign up request was already approved."))
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
                    token = SignUpToken.objects.filter(
                        user=get_user_model().objects.filter(email=obj.email).first()).first().token
                    self.message_user(request, _("Company saved. Link to register master account was sent."))
                    self.message_user(request, _(f"Registration link - 192.168.1.33:8000/create-account?token={token}"))
                    # TODO: Do not push test user message and token.
                except Exception as error:
                    self.message_user(request, _(
                        f"Company with provided phone number or tax id already exists. Additional info [{error}]"))
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if 'add' in request.META['PATH_INFO']:
            return ()
        else:
            return self.readonly_fields

    def type_choice(self, obj):
        choice = \
            next(filter(lambda x: x[0] == obj.type, Company.COMPANY_TYPE_CHOICES), Company.COMPANY_TYPE_CHOICES[0])[1]
        return _(choice)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "type":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in Company.COMPANY_TYPE_CHOICES]

        return super(SignUpRequestAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    type_choice.short_description = _('Company Type')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    readonly_fields = ('operation',
                       'rating',
                       'comment',
                       'date_created',
                       'reviewer')
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
        (_('Review info'), {
            'fields': (
                'rating',
                'comment',
                'reviewer',
                'operation',
            ),
        }),
        (_('Approved'), {
            'fields': (
                'approved',
            ),
        }),
    )

    def response_change(self, request, obj):
        if "_approve_review" in request.POST:
            if obj.approved:
                self.message_user(request, _("Review was already approved."))
            else:
                obj.approved = True
                obj.save()
                self.message_user(request, _("Review successfully approved."))
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if 'add' in request.META['PATH_INFO']:
            return ()
        else:
            return self.readonly_fields
