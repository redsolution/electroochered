# -*- coding: utf-8 -*-
INSTALLED_FORMATS = [
    ('sadiki.administrator.import_plugins.requestion.RequestionFormat', u'Импорт заявок'),
    ('sadiki.administrator.import_plugins.sadik_list.SadikListFormat', u'Импорт ДОУ'),
]

SADIKS_FORMATS = ['sadiki.administrator.import_plugins.sadik_list.SadikListFormat', ]

REQUESTION_FORMATS = [format[0] for format in INSTALLED_FORMATS if format[0] not in SADIKS_FORMATS]
