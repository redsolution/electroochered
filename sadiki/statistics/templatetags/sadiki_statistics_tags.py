# -*- coding: utf-8 -*-
from django import template
from sadiki.core.models import Requestion, STATUS_REQUESTER, \
    STATUS_ON_DISTRIBUTION, AgeGroup

register = template.Library()

@register.inclusion_tag("statistics/templatetags/requestion_statistics.html")
def requestions_statistics():
    requestions = Requestion.objects.filter(status__in=(STATUS_REQUESTER,
            STATUS_ON_DISTRIBUTION))
    age_groups = AgeGroup.objects.all()
    requestions_numbers_by_groups = []
    for group in age_groups:
        requestions_numbers_by_groups.append(
            requestions.filter_for_age(min_birth_date=group.min_birth_date(), max_birth_date=group.max_birth_date()).count())
    context = {
        'requestions_number': requestions.count(),
        'benefit_requestions_number': requestions.filter(
            benefit_category__priority__gt=0).count(),
        'groups': age_groups,
        'requestions_numbers_by_groups': requestions_numbers_by_groups
    }
    return context
