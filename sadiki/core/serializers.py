# -*- coding: utf-8 -*-
from rest_framework import serializers

from sadiki.core.models import Requestion, Sadik, AgeGroup, SadikGroup


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


class AgeGroupSerializer(serializers.ModelSerializer):
    max_birth_date = serializers.DateField(
        source='max_birth_date', format='%d.%m.%Y')
    min_birth_date = serializers.DateField(
        source='min_birth_date', format='%d.%m.%Y')

    class Meta:
        model = AgeGroup
        fields = ('id', 'name', 'short_name', 'max_birth_date',
                  'min_birth_date')
        read_only_fields = ('id', 'name', 'short_name')


class SadikGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SadikGroup
        fields = ('id', 'age_group', 'capacity', 'free_places', 'active')


class SadikSerializer(serializers.ModelSerializer):
    groups = SadikGroupSerializer(read_only=True, required=False, many=True)
    # groups = serializers.SerializerMethodField('active_groups')

    class Meta:
        model = Sadik
        fields = ('id', 'short_name', 'age_groups',
                  'active_registration', 'active_distribution', 'groups')
        read_only_fields = (
            'id', 'short_name', 'age_groups', 'active_registration',
            'active_distribution')

    def active_groups(self, obj):
        groups_qs = obj.groups.active()
        return SadikGroupSerializer(groups_qs, many=True).data
