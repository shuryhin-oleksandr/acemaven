from django.contrib import admin

from app.location.models import Country
from app.handling.models import GlobalFee, LocalFee, CommonFee
from app.handling.admin import ListTopFilter, RelatedListTopFilter

from django.utils.translation import ugettext_lazy as _


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'currency', 'is_main',)
    search_fields = ('name', 'code',)


@admin.register(GlobalFee)
class GlobalFeeAdmin(admin.ModelAdmin):
    change_list_template = 'handling/global_fee_change_list.html'
    list_display = ('shipping_mode', 'value_type', 'value', 'is_active',)
    radio_fields = {'value_type': admin.VERTICAL}
    list_editable = ('value', 'value_type', 'is_active',)
    list_filter = (
        ('fee_type', ListTopFilter),
    )
    ordering = ('-shipping_mode',)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        fee_type = request.GET.get('fee_type__exact', 'booking')
        queryset = super().get_queryset(request)
        if not self.has_view_or_change_permission(request):
            queryset = queryset.none()
        return queryset.filter(fee_type=fee_type)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "value_type":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in CommonFee.VALUE_TYPE_CHOICES]

        return super(GlobalFeeAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(LocalFee)
class LocalFeeAdmin(admin.ModelAdmin):
    change_list_template = 'handling/global_fee_change_list.html'
    list_display = ('fee_type', 'value', 'value_type_choice', 'shipping_mode', 'company', 'is_active',)
    search_fields = ('company__name', 'fee_type',)
    list_filter = (
        ('company', RelatedListTopFilter,),
        ('fee_type', ListTopFilter,),
    )

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "value_type":
            kwargs['choices'] = [(choice[0], _(choice[1])) for choice in CommonFee.VALUE_TYPE_CHOICES]

        return super(LocalFeeAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    def value_type_choice(self, obj):
        choice = \
            next(filter(lambda x: x[0] == obj.value_type, CommonFee.VALUE_TYPE_CHOICES), CommonFee.VALUE_TYPE_CHOICES[0])[1]
        return _(choice)

    value_type_choice.short_description = _('Value type')
