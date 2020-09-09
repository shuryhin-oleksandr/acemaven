from rest_framework import serializers

from app.core.models import SignUpRequest


class SignUpRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignUpRequest
        fields = (
            'type',
            'name',
            'address_line_first',
            'address_line_second',
            'state',
            'city',
            'zip_code',
            'phone',
            'tax_id',
            'employees_number',
            'website',
            'master_email',
        )
