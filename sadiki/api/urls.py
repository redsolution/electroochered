# -*- coding: utf-8 -*- 
from django.conf.urls import patterns, url, include

from sadiki.api.views import get_distributions, get_distribution, get_child, \
    api_sign_test, get_kindergartens, ChangeRequestionStatus, \
    GetRequestionsByResolution, get_evidience_documents, get_requestions, \
    RequestionsQueue, api_enc_test, get_simple_kindergtns, get_age_groups, \
    GroupsForSadikView

urlpatterns = patterns(
    '',
    # ДОУ
    url(r'^get_kg_info/', get_kindergartens),
    url(r'^sadik/simple_info/', get_simple_kindergtns),
    url(r'^sadik/(?P<sadik_id>\d{1,7})/groups/', GroupsForSadikView.as_view()),

    # Заявки
    url(r'^get_child/', get_child),
    url(r'^requestions_by_resolution/', GetRequestionsByResolution.as_view()),
    url(r'^change_requestion_status/', ChangeRequestionStatus.as_view()),
    url(r'^get_requestions/', RequestionsQueue.as_view()),

    # Распределения
    url(r'^get_distributions/$', get_distributions),
    url(r'^get_distribution/', get_distribution),

    # остальное
    url(r'^sign_test/', api_sign_test),
    url(r'^enc_test/', api_enc_test),
    url(r'^get_evidience_documents/', get_evidience_documents),
    url(r'^age_groups/', get_age_groups),
)
