# -*- coding: utf-8 -*-
from rest_framework import serializers

from sadiki.core.models import Requestion, Sadik, AgeGroup


class RequestionGeoSerializer(serializers.ModelSerializer):
    location = serializers.Field(source='location.tuple')

    class Meta:
        model = Requestion
        fields = ('id', 'requestion_number', 'location')


class AnonymRequestionGeoSerializer(serializers.ModelSerializer):
    location = serializers.Field(source='location.tuple')

    class Meta:
        model = Requestion
        fields = ('location', )


class SadikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sadik
        fields = ('id', 'short_name', 'age_groups')
        read_only_fields = fields


class AgeGroupSerializer(serializers.ModelSerializer):
    max_birth_date = serializers.Field(source='max_birth_date')
    min_birth_date = serializers.Field(source='min_birth_date')

    class Meta:
        model = AgeGroup
        fields = ('id', 'name', 'short_name', 'max_birth_date',
                  'min_birth_date')
        read_only_fields = ('id', 'name', 'short_name')
