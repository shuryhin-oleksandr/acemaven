from django.contrib import admin

from app.location.models import Country
from app.handling.models import GlobalFee, LocalFee
from app.handling.admin import ListTopFilter, RelatedListTopFilter


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


@admin.register(LocalFee)
class LocalFeeAdmin(admin.ModelAdmin):
    change_list_template = 'handling/global_fee_change_list.html'
    list_display = ('fee_type', 'value', 'value_type', 'shipping_mode', 'company', 'is_active',)
    search_fields = ('company__name', 'fee_type',)
    list_filter = (
        ('company', RelatedListTopFilter,),
        ('fee_type', ListTopFilter,),
    )
