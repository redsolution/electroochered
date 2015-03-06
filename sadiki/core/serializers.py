# -*- coding: utf-8 -*-
from rest_framework import serializers

from sadiki.core.models import Requestion


class RequestionGeoSerializer(serializers.ModelSerializer):
    location = serializers.Field(source='location.tuple')

    class Meta:
        model = Requestion
        fields = ('id', 'requestion_number', 'location')