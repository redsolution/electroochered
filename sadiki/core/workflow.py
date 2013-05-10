# -*- coding: utf-8 -*-
from django.template.base import Template
from sadiki.conf_settings import TEMP_DISTRIBUTION, IMMEDIATELY_DISTRIBUTION, ETICKET
from sadiki.core.models import *
from sadiki.core.permissions import OPERATOR_PERMISSION, DISTRIBUTOR_PERMISSION, REQUESTER_PERMISSION, SUPERVISOR_PERMISSION
from sadiki.core.settings import *
from sadiki.logger.models import ACCOUNT_LOG, ANONYM_LOG, OPERATOR_LOG


class Transition(object):
    u"""
    Модель перехода в workflow.

    Поля:

    - ``src`` - начальный статус заявки
    - ``dst`` - конечный статус заявки
    - ``index`` - номер перехода
    - ``comment`` - комментарий (название) перехода
    - ``permissions`` - список прав, для кого доступна возможность делать этот переход
    - ``permission_callback`` - опциональная функция для проверки возможности перехода.

    Т.к. система не предусматривает прав для анонимных пользователей,
    для публичной доступности перехода необходимо указать значение ``Transition.ANONYMOUS_PERMISSION``.

    В случае, если список ``permissions`` пустой, переход автоматический, никому не доступен.

    В функцию ``permission_callback`` передаются аргументы: user, requestion, transition,
    request, form параметры user, request и form не обязательные::

        def perm_callback(requestion, transition, user=None, request=None, form=None):
    """

    ANONYMOUS_PERMISSION = '*'

    def __init__(self, src, dst, transition, comment, permissions, permission_callback=None):
        self.src = src
        self.dst = dst
        self.index = transition
        self.comment = comment
        self.required_permissions = permissions
        self.permission_cb = permission_callback
        self.confirmation_form_class = None


class Workflow(object):
    def __init__(self):
        self.transitions = []
        super(Workflow, self).__init__()

    def add(self, src, dst, transition, comment=u'', permissions=None, permission_callback=None):
        #проверим, что у нас нет повторяющихся id переходов
        if permissions is None:
            permissions = []
        if [tr for tr in self.transitions if tr.index == transition]:
            raise AttributeError('Transition with id=%d already added' % transition)
        self.transitions.append(Transition(src, dst, transition, comment, permissions, permission_callback))

    def available_transition_statuses(self, src):
        u"""
        Возвращает коды статусов, в которые можно перейти из указанного
        """
        transitions = filter(lambda t: t.src == src, self.transitions)
        return [t.dst for t in transitions]

    def available_transitions(self, src=None, dst=None):
        u"""
        Возвращает коды возможных переходов изменения статуса
        """
        transitions = self.transitions
        if src is not None and dst is not None:
            transitions = filter(lambda t: t.src == src and t.dst == dst, self.transitions)
        elif src is not None:
            transitions = filter(lambda t: t.src == src, self.transitions)
        elif dst is not None:
            transitions = filter(lambda t: t.dst == dst, transitions)
        return [t.index for t in transitions]

    def get_transition_by_index(self, index):
        transitions = filter(lambda t: t.index == index, self.transitions)
        if transitions:
            return transitions[0]
        else:
            return None

# Изменение статуса заявки()
REQUESTION_REGISTRATION = 0             # Регистрация через оператора
REQUESTION_IMPORT = 1                   # Импорт заявки
ADD_REQUESTION = 2                      # Добавление заявки пользователем
CONFIRM_REQUESTION = 3                  # Документальное подтверждение заявки
ON_DISTRIBUTION = 5                     # Переход в комплектование
DECISION = 6                            # Выделено место
ON_DISTRIBUTION_RETURN = 7              # возврат в очередь нераспределенных
IMMEDIATELY_DECISION = 8                # Выделено место(немедленное зачисление)
ON_TEMP_DISTRIBUTION = 12               # Переход в комплектование временно зачисленной заявки
ON_TEMP_DISTRIBUTION_RETURN = 58        # Возврат в очередь нераспределенной временно зач-й
PERMANENT_DECISION = 13                 # Выделение места временно зачисленному
IMMEDIATELY_PERMANENT_DECISION = 14     # Выделение места временно зачисленному(немедленное зач-е)
IMMEDIATELY_PERMANENT_DECISION = 15     # Выделение места временно зачисленному(немедленное зач-е)
DECISION_DISTRIBUTION = 16              # Зачислен
DECISION_ABSENT = 17                    # Невозможно установить контакт
DECISION_NOT_APPEAR = 18                # Неявка в ДОУ
ABSENT_DISTRIBUTED = 19                 # Явка в допольнительное время
NOT_APPEAR_DISTRIBUTED = 20             # Явка в дополнительное время
PASS_GRANTED = 21                       # Выдача путевки
PASS_DISTRIBUTED = 22                   # Зачисление по путевке
PASS_NOT_APPEAR = 23                    # Неявка по путевке
TEMP_DISTRIBUTION_TRANSFER = 35         # Временно зачислен
TEMP_PASS_TRANSFER = 36                 # Выдана путевка для временного зачисления
TEMP_PASS_DISTRIBUTION = 37             # Временное зачисление по путевке
REQUESTER_REMOVE_REGISTRATION = 38      # Снятие с учета подтвержденной заявки
NOT_CONFIRMED_REMOVE_REGISTRATION = 39  # Снятие с учета неподтвержденной заявки
RESTORE_REQUESTION = 40                 # Восстановить заявку
ABSENT_REMOVE_REGISTRATION = 41         # Снять с учета при невозможности связаться
NOT_APPEAR_REMOVE_REGISTRATION = 42     # Снять с учета при неявке
REMOVE_REGISTRATION_ARCHIVE = 43        # Помещение снятой заявки в архив
DISTRIBUTED_ARCHIVE = 44                # Помещение распределенной заявки в архив
DECISION_REQUESTER = 46                 # Отказ от места в ДОУ
NOT_APPEAR_REQUESTER = 52               # Возврат в очередь после неявки
ABSENT_REQUESTER = 53                   # Возврат в очередь при невозможности связаться
PASS_GRANTED_REQUESTER = 47             # Возврат путевки
RETURN_TEMP_DISTRIBUTED = 48            # Возврат в очередь временно зачисленной заявки
RETURN_TEMP_PASS_TRANSFER = 49          # Возврат временной путевки
ABSENT_EXPIRE = 50                      # Истечение сроков обжалования
NOT_APPEAR_EXPIRE = 51                  # Истечение сроков обжалования
REQUESTION_REJECT = 55                  # Истечение сроков на подтверждение документов
TEMP_ABSENT = 56                        # Длительное отсутствие по уважительной причине
TEMP_ABSENT_CANCEL = 57                 # Возврат после отсутсвия по уважительной причине
#отказ от зачилсения на постоянной основе
DECISION_TEMP_DISTRIBUTED = 62      # Отказ от места в ДОУ
NOT_APPEAR_TEMP_DISTRIBUTED = 63    # Отказ от места в ДОУ после неявки
ABSENT_TEMP_DISTRIBUTED = 64        # Отказ от места в ДОУ после невозожности связаться 


workflow = Workflow()

# 1) Подача заявления
workflow.add(None, STATUS_REQUESTER_NOT_CONFIRMED, ADD_REQUESTION,
    u'Самостоятельная регистрация',)
workflow.add(None, STATUS_REQUESTER, REQUESTION_IMPORT, u'Импорт заявки')
workflow.add(None, STATUS_REQUESTER, REQUESTION_REGISTRATION,
    u'Регистрация через оператора',)
workflow.add(STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REQUESTER, CONFIRM_REQUESTION,
    u'Подтверждение документов', permissions=[OPERATOR_PERMISSION[0]])

# 2) Комплектование
# 2.1) Очередники
workflow.add(STATUS_REQUESTER, STATUS_ON_DISTRIBUTION, ON_DISTRIBUTION,
    u'Перевод в комплектование')
workflow.add(STATUS_ON_DISTRIBUTION, STATUS_DECISION, DECISION,
    u'Выделение места в ДОУ')
workflow.add(STATUS_ON_DISTRIBUTION, STATUS_REQUESTER, ON_DISTRIBUTION_RETURN,
    u'Возврат в очередь нераспределенных')
# Немедленное зачисление
if IMMEDIATELY_DISTRIBUTION != IMMEDIATELY_DISTRIBUTION_NO:
    workflow.add(STATUS_REQUESTER, STATUS_DECISION, IMMEDIATELY_DECISION,
        u'Выделение места в ДОУ (немедленное зачисление)', permissions=[DISTRIBUTOR_PERMISSION[0]])


# 2.3) Временное зачисление
if TEMP_DISTRIBUTION == TEMP_DISTRIBUTION_YES:
    workflow.add(STATUS_TEMP_DISTRIBUTED, STATUS_ON_TEMP_DISTRIBUTION,
        ON_TEMP_DISTRIBUTION,
        u'Комплектование временно зачисленных')
    workflow.add(STATUS_ON_TEMP_DISTRIBUTION, STATUS_TEMP_DISTRIBUTED,
        ON_TEMP_DISTRIBUTION_RETURN,
        u'Возврат нераспределенных в очередь(временно зачисленные)')
    workflow.add(STATUS_ON_TEMP_DISTRIBUTION, STATUS_DECISION,
        PERMANENT_DECISION, u'Выделение места в ДОУ на постоянное основе')
    # Немедленное зачисление
    if IMMEDIATELY_DISTRIBUTION != IMMEDIATELY_DISTRIBUTION_NO:
        workflow.add(STATUS_TEMP_DISTRIBUTED, STATUS_DECISION,
            IMMEDIATELY_PERMANENT_DECISION,
            u'Выделение места в ДОУ на постоянной основе(немедленное зачисление)', permissions=[DISTRIBUTOR_PERMISSION[0]])


# 3) Зачисление
# 3.1) Очередники
workflow.add(STATUS_DECISION, STATUS_DISTRIBUTED, DECISION_DISTRIBUTION,
             u'Зачисление', permissions=[DISTRIBUTOR_PERMISSION[0]])
workflow.add(STATUS_DECISION, STATUS_ABSENT, DECISION_ABSENT,
             u'Невозможно установить контакт с заявителем', permissions=[DISTRIBUTOR_PERMISSION[0]])
workflow.add(STATUS_DECISION, STATUS_NOT_APPEAR, DECISION_NOT_APPEAR,
             u'Неявка в ДОУ', permissions=[DISTRIBUTOR_PERMISSION[0]])
workflow.add(STATUS_ABSENT, STATUS_DISTRIBUTED, ABSENT_DISTRIBUTED,
             u'Явка в дополнительное время отсутствующих', permissions=[DISTRIBUTOR_PERMISSION[0]])
workflow.add(STATUS_NOT_APPEAR, STATUS_DISTRIBUTED, NOT_APPEAR_DISTRIBUTED,
             u'Явка в дополнительное время неявившихся', permissions=[DISTRIBUTOR_PERMISSION[0]])
# Путевки
if ETICKET != ETICKET_NO:
    workflow.add(STATUS_DECISION, STATUS_PASS_GRANTED, PASS_GRANTED,
        u'Получение путевки', permissions=[DISTRIBUTOR_PERMISSION[0]])
    workflow.add(STATUS_PASS_GRANTED, STATUS_DISTRIBUTED, PASS_DISTRIBUTED,
        u'Зачисление по путевке', permissions=[DISTRIBUTOR_PERMISSION[0]])
    workflow.add(STATUS_PASS_GRANTED, STATUS_NOT_APPEAR, PASS_NOT_APPEAR,
        u'Неявка в ДОУ с путевкой', permissions=[DISTRIBUTOR_PERMISSION[0]])

# 3.3) Временное зачисление
if TEMP_DISTRIBUTION == TEMP_DISTRIBUTION_YES:
#    зачисление на постоянной основе
#    временное зачисление
    workflow.add(STATUS_REQUESTER, STATUS_TEMP_DISTRIBUTED,
        TEMP_DISTRIBUTION_TRANSFER, u'Временное зачисление', permissions=[DISTRIBUTOR_PERMISSION[0]])
    # Путевки для временного зачисления
    if ETICKET != ETICKET_NO:
        workflow.add(STATUS_REQUESTER, STATUS_TEMP_PASS_TRANSFER,
            TEMP_PASS_TRANSFER, u'Выдача временной путевки', permissions=[DISTRIBUTOR_PERMISSION[0]])
        workflow.add(STATUS_TEMP_PASS_TRANSFER, STATUS_TEMP_DISTRIBUTED,
            TEMP_PASS_DISTRIBUTION, u'Временное зачисление по путевке', permissions=[DISTRIBUTOR_PERMISSION[0]])

# 4) Отказы

workflow.add(STATUS_REQUESTER, STATUS_REMOVE_REGISTRATION,
    REQUESTER_REMOVE_REGISTRATION, u'Снятие с учёта', permissions=[OPERATOR_PERMISSION[0]])
workflow.add(STATUS_REMOVE_REGISTRATION, STATUS_REQUESTER,
    RESTORE_REQUESTION, u'Восстановление в очереди', permissions=[SUPERVISOR_PERMISSION[0]])
workflow.add(STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REMOVE_REGISTRATION,
    NOT_CONFIRMED_REMOVE_REGISTRATION, u'Отклонение документов', permissions=[OPERATOR_PERMISSION[0]])
workflow.add(STATUS_ABSENT, STATUS_ABSENT_EXPIRE, ABSENT_EXPIRE,
    u'Истечение сроков на обжалование отсутствия')
workflow.add(STATUS_ABSENT_EXPIRE, STATUS_REMOVE_REGISTRATION,
    ABSENT_REMOVE_REGISTRATION,
    u'Снятие с учёта по истечению срока на установление контакта', permissions=[OPERATOR_PERMISSION[0]])
workflow.add(STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE, NOT_APPEAR_EXPIRE,
    u'Истечение сроков на обжалование неявки')
workflow.add(STATUS_NOT_APPEAR_EXPIRE, STATUS_REMOVE_REGISTRATION,
    NOT_APPEAR_REMOVE_REGISTRATION, u'Снятие с учёта по истечению срока явки', permissions=[OPERATOR_PERMISSION[0]])

workflow.add(STATUS_REMOVE_REGISTRATION, STATUS_ARCHIVE,
    REMOVE_REGISTRATION_ARCHIVE, u'Архивация снятых с учёта')
workflow.add(STATUS_DISTRIBUTED, STATUS_ARCHIVE, DISTRIBUTED_ARCHIVE,
    u'Архивация зачисленных')

workflow.add(STATUS_DECISION, STATUS_REQUESTER, DECISION_REQUESTER,
    u'Отказ от места в ДОУ', permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]])
workflow.add(STATUS_NOT_APPEAR, STATUS_REQUESTER, NOT_APPEAR_REQUESTER,
    u'Отказ от места в ДОУ после неявки', permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]])
workflow.add(STATUS_ABSENT, STATUS_REQUESTER, ABSENT_REQUESTER,
    u'Отказ от места в ДОУ после отсутствия', permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]])
workflow.add(STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REJECTED,
    REQUESTION_REJECT, u'Истечение сроков на подтверждение документов')


# отказ от зачисления на постоянной основе
if TEMP_DISTRIBUTION == TEMP_DISTRIBUTION_YES:
    workflow.add(STATUS_DECISION, STATUS_TEMP_DISTRIBUTED,
        DECISION_TEMP_DISTRIBUTED,
        u'Отказ от места в ДОУ на постоянное основе',
        permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]])
    workflow.add(STATUS_NOT_APPEAR, STATUS_TEMP_DISTRIBUTED,
        NOT_APPEAR_TEMP_DISTRIBUTED,
        u'Отказ от места в ДОУ на постоянной основе после неявки',
        permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]])
    workflow.add(STATUS_ABSENT, STATUS_TEMP_DISTRIBUTED,
        ABSENT_TEMP_DISTRIBUTED,
        u'Отказ от места в ДОУ на постоянной основе после отсутствия',
        permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]])

# Путевки
if ETICKET != ETICKET_NO:
    workflow.add(STATUS_PASS_GRANTED, STATUS_REQUESTER, PASS_GRANTED_REQUESTER,
        u'Возврат путевки', permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]])

# Временное зачисление
if TEMP_DISTRIBUTION == TEMP_DISTRIBUTION_YES:
    workflow.add(STATUS_DISTRIBUTED, STATUS_TEMP_ABSENT, TEMP_ABSENT,
        u"Длительное отсутствие по уважительной причине", permissions=[OPERATOR_PERMISSION[0]])
    workflow.add(STATUS_TEMP_ABSENT, STATUS_DISTRIBUTED, TEMP_ABSENT_CANCEL,
        u"Возврат после отсутствия по уважительной причине", permissions=[OPERATOR_PERMISSION[0]])
    workflow.add(STATUS_TEMP_DISTRIBUTED, STATUS_REQUESTER,
        RETURN_TEMP_DISTRIBUTED, u'Возвращение в очередь из временно зачисленных', permissions=[OPERATOR_PERMISSION[0]])
    # Путевки
    if ETICKET != ETICKET_NO:
        workflow.add(STATUS_TEMP_PASS_TRANSFER, STATUS_REQUESTER,
            RETURN_TEMP_PASS_TRANSFER, u'Возврат временной путевки', permissions=[OPERATOR_PERMISSION[0]])

#Изменение данных заявки
CHANGE_REQUESTION = 71
CHANGE_REQUESTION_BY_OPERATOR = 72
CHANGE_ADMISSION_DATE = 73
CHANGE_ADMISSION_DATE_BY_OPERATOR = 74
CHANGE_PROFILE = 75
CHANGE_PROFILE_BY_OPERATOR = 76
CHANGE_PREFERRED_SADIKS = 77
CHANGE_PREFERRED_SADIKS_BY_OPERATOR = 78
CHANGE_REGISTRATION_DATETIME = 79
CHANGE_BIRTHDATE = 80
CHANGE_BENEFITS = 81
CHANGE_BENEFITS_BY_OPERATOR = 82
CHANGE_DOCUMENTS = 83
CHANGE_DOCUMENTS_BY_OPERATOR = 84
CREATE_PROFILE = 85
CREATE_PROFILE_BY_OPERATOR = 86
IMPORT_PROFILE = 87
EMBED_REQUESTION_TO_PROFILE = 88


#Распределение
DISTRIBUTION_INIT = 100
DISTRIBUTION_AUTO = 103
DISTRIBUTION_START = 101
DISTRIBUTION_END = 102

#Изменение данных ДОУ
CHANGE_SADIK_GROUP_PLACES = 104
CHANGE_SADIK_INFO = 105

#изменение путевки
VACANCY_DISTRIBUTED = 110

START_NEW_YEAR = 106

DISABLE_EMAIL_ACTIONS = [DECISION, PERMANENT_DECISION]

ACTION_CHOICES = [(transition.index, transition.comment) for transition in
                    workflow.transitions]

ACTION_CHOICES.extend(
#    добавляем действия с заявками
    [(CHANGE_REQUESTION, u"Изменение заявки пользователем"),
    (CHANGE_REQUESTION_BY_OPERATOR, u"Изменение заявки оператором"),
    (CHANGE_ADMISSION_DATE, u"Изменение ЖДП"),
    (CHANGE_ADMISSION_DATE_BY_OPERATOR, u"Изменение ЖДП оператором"),
    (CHANGE_PROFILE, u"Изменение профиля пользователем"),
    (CHANGE_PROFILE_BY_OPERATOR, u"Изменение профиля оператором"),
    (CHANGE_PREFERRED_SADIKS, u"Изменение приоритетных ДОУ пользователем"),
    (CHANGE_PREFERRED_SADIKS_BY_OPERATOR,
        u"Изменение приоритетных ДОУ оператором"),
    (CHANGE_REGISTRATION_DATETIME, u"Изменение даты регистрации"),
    (CHANGE_BIRTHDATE, u"Изменение даты рождения"),
    (CHANGE_BENEFITS, u"Изменение льгот"),
    (CHANGE_BENEFITS_BY_OPERATOR, u"Изменение льгот оператором"),
    (CHANGE_DOCUMENTS, u"Изменение документов"),
    (CHANGE_DOCUMENTS_BY_OPERATOR, u"Изменение документов оператором"),
    (CREATE_PROFILE, u"Регистрация профиля"),
    (CREATE_PROFILE_BY_OPERATOR, u"Регистрация профиля оператором"),
    (IMPORT_PROFILE, u"Импорт профиля"),
    (EMBED_REQUESTION_TO_PROFILE, u"Прикрепление заявки к профилю"),
#    Распределения
    (DISTRIBUTION_INIT, u'Начало распределения'),
    (DISTRIBUTION_AUTO, u'Начало автоматического комплектования'),
    (DISTRIBUTION_START, u'Начало ручного комплектования'),
    (DISTRIBUTION_END, u'Завершение распределения'),
#    ДОУ
    (CHANGE_SADIK_GROUP_PLACES, u'Изменение мест в группу ДОУ'),
    (CHANGE_SADIK_INFO, u'Изменение информации о ДОУ'),
    (START_NEW_YEAR, u'Начало нового учебного года'),
#    Путевки
    (VACANCY_DISTRIBUTED, u'Завершено выделение места'),
    ]
)

ACTION_TEMPLATES = dict(
    [(transition.index, {ANONYM_LOG:Template(u"")})
        for transition in workflow.transitions]
)

#переопределеяем стандартные шаблоны для действий с заявкой

document_confirmation_template = u"""
        Заявки с таким же идентифицируюим документом были сняты с учета:
        {% for requestion in other_requestions %}
            {{ requestion }}{% if not forloop.last %}; {% endif %}
        {% endfor %}"""

ACTION_TEMPLATES.update({
    NOT_CONFIRMED_REMOVE_REGISTRATION:{
        ANONYM_LOG:Template(u""),
        OPERATOR_LOG:Template(u"""Заявка {{ other_requestion }} с таким же идентифицирующим документом была документально подтверждена"""),
    },
    CONFIRM_REQUESTION:{
        ANONYM_LOG:Template(u""),
        OPERATOR_LOG:Template(document_confirmation_template),
    },
    RESTORE_REQUESTION:{
        ANONYM_LOG:Template(u""),
        OPERATOR_LOG:Template(document_confirmation_template),
        },
})

requestion_account_template = u"""
    {% if requestion.sex %}Пол: {{ requestion.get_sex_display }};{% endif %}
    {% if requestion.name %}Имя: {{ requestion.name }};{% endif %}
    {% if requestion.comment %}Комментарий: {{ requestion.comment }};{% endif %}
    {% if requestion.template %}Тип документа: {{ requestion.template }};{% endif %}
    {% if requestion.document_number %}Номер документа: {{ requestion.document_number }};{% endif %}
    {% if requestion.location %}Местоположение: {{ requestion.location.x }}, {{ requestion.location.y }};{% endif %}
    """

requestion_anonym_template = u"""
    Территориальные области:
    {% for area in areas %}
        {{ area }};
    {% empty %}
        Весь муниципалитет;
    {% endfor %}
    {% if requestion.birth_date %}Дата рождения: {{ requestion.birth_date }};{% endif %}
    {% if not requestion.distribute_in_any_sadik == None %}Зачислять в любой ДОУ: {{ requestion.distribute_in_any_sadik|yesno:"Да, Нет" }};{% endif %}
    {% if requestion.admission_date %}Желаемый год поступления: {{ requestion.admission_date.year }};{% endif %}
    {% if pref_sadiks %}
        Приоритетные МДОУ: {% for sadik in pref_sadiks %}{{ sadik }};{% endfor %}
    {% endif %}
    """

registration_account_template = u"""
    {% if user.email %}Электронная почта:{{ user.email }}{% endif %}
    {% if profile.nickname %}Псевдоним: {{ profile.nickname }};{% endif %}
    {% if profile.phone_number %}Основной телефон: {{ profile.phone_number }};{% endif %}
    {% if profile.mobile_number %}Дополнительный телефон: {{ profile.mobile_number }};{% endif %}
    {% with profile.get_identity_documents as document %}
        {% if document %}
            Тип документа: {{ document.template }};
            Номер документа: {{ document.document_number }};
        {% endif %}
    {% endwith %}
    """

change_profile_account_template = u'''
    {% if "nickname" in changed_data %}Псевдоним: {{ profile.nickname }};{% endif %}
    {% if "phone_number" in changed_data %}Телефон: {{ profile.phone_number }};{% endif %}
    {% if "mobile_number" in changed_data %}Мобильный телефон: {{ profile.mobile_number }};{% endif %}
    '''

change_preferred_sadiks_anonym_template = u'''
    {% if "pref_sadiks" in changed_data %}
        Приоритетные МДОУ: {% for sadik in pref_sadiks %}{{ sadik }}; {% endfor %}
    {% endif %}
    {% if "distribute_in_any_sadik" in changed_data %}Зачислять в любой ДОУ: {{ distribute_in_any_sadik|yesno:"да,нет" }};{% endif %}
    '''

change_benefits_anonym_template = u"""
    Основная категория льгот: {{ requestion.benefit_category }};
    """

change_benefits_account_template = u"""
    {% if benefits %}
        Льготы: {% for benefit in benefits %}{{ benefit }}; {% endfor %}
    {% endif %}
    """

change_documents_account_template = u"""
    {% if benefit_documents %}
        Документы для льгот:
        {% for document in benefit_documents %}
            {{ document.document_number }} ({{ document.template }});
        {% endfor %}.
    {% endif %}
    {% if requestion_documents %}
        Документы для льгот:
        {% for document in requestion_documents %}
            {{ document.document_number }} ({{ document.template }});
        {% endfor %}.
    {% endif %}
    """

ACTION_TEMPLATES.update({
    ADD_REQUESTION:{
        ACCOUNT_LOG:Template(requestion_account_template + change_benefits_account_template),
        ANONYM_LOG:Template(requestion_anonym_template + change_benefits_anonym_template)
    },
    CREATE_PROFILE:{
        ACCOUNT_LOG: Template(registration_account_template),
    },
    CREATE_PROFILE_BY_OPERATOR:{
        ACCOUNT_LOG: Template(registration_account_template),
    },
    REQUESTION_REGISTRATION:{
        ACCOUNT_LOG: Template(requestion_account_template + change_benefits_account_template),
        ANONYM_LOG: Template(requestion_anonym_template + change_benefits_anonym_template),
    },
    IMPORT_PROFILE:{
        ACCOUNT_LOG: Template(registration_account_template),
    },
    REQUESTION_IMPORT:{
        ACCOUNT_LOG: Template(requestion_account_template + change_benefits_account_template),
        ANONYM_LOG: Template(requestion_anonym_template + change_benefits_anonym_template),
    },
    CHANGE_REQUESTION: {
        ANONYM_LOG:Template(u'''
                    {% if "admission_date" in changed_fields %}Желаемый год поступления: {{ requestion.admission_date.year }};{% endif %}
                    '''),
        ACCOUNT_LOG:Template(u'''
                    {% if "sex" in changed_fields %}Пол: {{ requestion.get_sex_display }};{% endif %}
                    {% if "name" in changed_fields %}Имя: {{ requestion.name }};{% endif %}
                    {% if "comment" in changed_fields %}Комментарий: {{ requestion.comment }};{% endif %}
                    {% if "location" in changed_fields %}Местоположение: {{ requestion.location.x }}, {{ requestion.location.y }};{% endif %}
                    '''),
        },
    CHANGE_REQUESTION_BY_OPERATOR: {
        ANONYM_LOG:Template(u'''
                    {% if "admission_date" in changed_fields %}Желаемый год поступления: {{ requestion.admission_date.year }};{% endif %}
                    '''),
        ACCOUNT_LOG:Template(u'''
                    {% if "sex" in changed_fields %}Пол: {{ requestion.get_sex_display }};{% endif %}
                    {% if "name" in changed_fields %}Имя: {{ requestion.name }};{% endif %}
                    {% if "comment" in changed_fields %}Комментарий: {{ requestion.comment }};{% endif %}
                    {% if "location" in changed_fields %}Местоположение: {{ requestion.location.x }}, {{ requestion.location.y }};{% endif %}
                    '''),
        },
    CHANGE_PROFILE: {
        ACCOUNT_LOG: Template(change_profile_account_template),
        },
    CHANGE_PROFILE_BY_OPERATOR: {
        ACCOUNT_LOG: Template(change_profile_account_template),
        },
    CHANGE_PREFERRED_SADIKS: {
        ANONYM_LOG: Template(change_preferred_sadiks_anonym_template)
    },
    CHANGE_PREFERRED_SADIKS_BY_OPERATOR: {
        ANONYM_LOG: Template(change_preferred_sadiks_anonym_template)
    },
    CHANGE_BENEFITS: {
        ANONYM_LOG: Template(change_benefits_anonym_template),
        ACCOUNT_LOG: Template(change_benefits_account_template),
    },
    CHANGE_BENEFITS_BY_OPERATOR: {
        ANONYM_LOG: Template(change_benefits_anonym_template),
        ACCOUNT_LOG: Template(change_benefits_account_template),
    },
    CHANGE_DOCUMENTS: {
        ACCOUNT_LOG: Template(change_documents_account_template),
    },
    CHANGE_DOCUMENTS_BY_OPERATOR: {
        ACCOUNT_LOG: Template(change_documents_account_template),
    },
    DISTRIBUTION_INIT:{
        OPERATOR_LOG: Template(u'''Распеределение создано''')
    },
    DISTRIBUTION_START:{
        OPERATOR_LOG: Template(u'''Распеределение начато''')
    },
    DISTRIBUTION_END:{
        OPERATOR_LOG: Template(u'''Распеределение завершено''')
    },
    CHANGE_REGISTRATION_DATETIME:{
        ANONYM_LOG: Template(u"""Дата регистрации изменена на {{ registration_datetime }}""")
    },
    CHANGE_BIRTHDATE:{
        ANONYM_LOG: Template(u"""Дата рождения изменена на {{ birth_date }}""")
    },
    CHANGE_SADIK_GROUP_PLACES:{
        ANONYM_LOG: Template(u"""Свободных мест:{{ sadik_group.free_places }}; Всего мест:{{ sadik_group.capacity }}""")
    },
    CHANGE_SADIK_INFO:{
        ANONYM_LOG: Template(u"""
            {% if 'postindex' in changed_data or 'street' in changed_data or 'building_number' in changed_data %}
            Индекс: {{ cleaned_data.postindex }}. Улица: {{ cleaned_data.street }}. Дом: {{ cleaned_data.building_number }}
            {% endif %}
            {% if 'email' in changed_data %}Электронная почта: {{ sadik.email }}{% endif %}
            {% if 'site' in changed_data %}Сайт: {{ sadik.site }}{% endif %}
            {% if 'head_name' in changed_data %}ФИО директора(заведующей): {{ sadik.head_name }}{% endif %}
            {% if 'phone' in changed_data %}Телефон: {{ sadik.phone }}{% endif %}
            {% if 'cast' in changed_data %}тип(категория) ДОУ: {{ sadik.cast }}{% endif %}
            {% if 'tech_level' in changed_data %}техническая оснащенность: {{ sadik.tech_level }}{% endif %}
            {% if 'training_program' in changed_data %}учебные программы дополнительного образования: {{ sadik.training_program }}{% endif %}
            {% if 'route_info' in changed_data %}Схема проезда изменена{% endif %}
            {% if 'extended_info' in changed_data %}дополнительная информация в формате HTML: {{ sadik.extended_info }}{% endif %}
            {% if 'active_registration' in changed_data %}ДОУ может быть указан как приоритетный: {{ sadik.active_registration|yesno:"да,нет" }}{% endif %}
            {% if 'active_distribution' in changed_data %}ДОУ принимает участие в распределении: {{ sadik.active_distribution|yesno:"да,нет" }}{% endif %}
            {% if 'age_groups' in changed_data %}Возрастные группы в ДОУ: {% for age_group in cleaned_data.age_groups %}{{ age_group }};{% endfor %}{% endif %}
        """)
    },
    VACANCY_DISTRIBUTED: {
        ANONYM_LOG: Template(u"""
            Было завершено выделение места в {{ sadik }}
        """)
    }
})

