from django.contrib import admin
from django.db import transaction
from django.forms import model_to_dict
from django.http import HttpResponseRedirect

from app.core.models import CustomUser, Company, BankAccount, Role, SignUpRequest, SignUpToken
from app.core.utils import master_account_processing


admin.site.register(CustomUser)
admin.site.register(Company)
admin.site.register(BankAccount)
admin.site.register(Role)
admin.site.register(SignUpToken)


@admin.register(SignUpRequest)
class SignUpRequestAdmin(admin.ModelAdmin):
    change_form_template = 'core/sign_up_request_changeform.html'

    def response_change(self, request, obj):
        if "_company_sign_up" in request.POST:
            try:
                with transaction.atomic():
                    company_info = model_to_dict(obj, exclude=['id', 'master_email'])
                    company = Company.objects.create(**company_info)
                    master_account_processing(company, obj.master_email)
                self.message_user(request, "Company saved. Link to register master account was sent.")
            except Exception:
                self.message_user(request, "Company with provided phone number already exists.")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)
