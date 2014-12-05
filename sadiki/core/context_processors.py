# -*- coding: utf-8 -*-
import os
import datetime
import csv
import getpass
import urllib2

from django.conf import settings

from sadiki.core import models as core_models
from sadiki.core.models import Preference, PREFERENCE_SECTION_MUNICIPALITY, PREFERENCE_MUNICIPALITY_PHONE, \
    PREFERENCE_MUNICIPALITY_NAME_GENITIVE


def constants(request):
    u"""
    Нам нужны все варианты для полей с атрибутом choice,
    например статусы заявки
    В шаблон передаются все объекты типа int из файла моделей модуля core
    """
    all_members = dir(core_models)
    int_constants = filter(lambda a: type(getattr(core_models, a)) is int, all_members)

    return dict((attr_name, getattr(core_models, attr_name)) for attr_name in int_constants)


def municipality_settings(request):
    u"""Все элементы конфигурационного файла из раздела municipality передаются в шаблон"""
    try:
        MUNICIPALITY_NAME_GENITIVE = Preference.objects.get(section=PREFERENCE_SECTION_MUNICIPALITY,
            key=PREFERENCE_MUNICIPALITY_NAME_GENITIVE)
    except Preference.DoesNotExist:
        MUNICIPALITY_NAME_GENITIVE = None
    try:
        MUNICIPALITY_PHONE = Preference.objects.get(section=PREFERENCE_SECTION_MUNICIPALITY,
            key=PREFERENCE_MUNICIPALITY_PHONE)
    except Preference.DoesNotExist:
        MUNICIPALITY_PHONE = None
    return {'MUNICIPALITY_NAME_GENITIVE': MUNICIPALITY_NAME_GENITIVE, 'MUNICIPALITY_PHONE': MUNICIPALITY_PHONE}


def get_csv():
    url = "https://docs.google.com/spreadsheet/pub?key=0AibgW8ZCe85QdHpKeFlSRXNFblpLcE1JY3BOV0k3MEE&output=csv"
    try:
        response = urllib2.urlopen(url)
        return csv.reader(response)
    except Exception:
        return None


def write_informer_block(messages, path_to_html):
    html_file = open(path_to_html, 'w')
    html_file.write("""
    <div class="header_warn">
        <div id="alert_msg" class="alert alert-warning alert-dismissable">
            <button type="button" class="close" data-dismiss="alert" aria-hidden="true"
            onclick="alert_dismiss()">&times;</button>
            <strong>Внимание!</strong> {0}
        </div>
    </div>""".format('<br>'.join(messages)))
    html_file.close()


def is_modified_recently(path_to_html):
    file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(path_to_html))
    return ((datetime.datetime.now() - file_modified).seconds / 3600.0) < 1


def get_notifier(request):
    messages = []
    try:
        instance_name = getpass.getuser()
        path_to_html = os.path.join('/srv/', instance_name, 'django', 'templates', 'includes', 'notifier.html')
        if os.path.isfile(path_to_html) and is_modified_recently(path_to_html):
            return {'msgs': messages}

        csv_file = get_csv()
        if not csv_file:
            return {'msgs': messages}

        for row in get_csv():
            if instance_name == row[0]:
                if ((len(row) > 2 and not row[2]) or len(row) == 2) and row[1]:
                    messages.append(row[1])

        if len(messages) > 0:
            write_informer_block(messages, path_to_html)
        else:
            open(path_to_html, 'w').close()
        return {'msgs': messages}
    except Exception:
        return {'msgs': messages}


def get_special_apps(request):
    special_apps_list = []
    if 'smevfms' in settings.INSTALLED_APPS:
        special_apps_list.append('smevfms')
    return {'special_apps': special_apps_list}