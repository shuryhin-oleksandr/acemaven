from rest_framework import serializers

from app.booking.models import AdditionalSurcharge


class AdditionalSurchargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalSurcharge
        fields = (
            'id',
            'title',
        )
