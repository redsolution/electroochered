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
    - ``permissions`` - список прав, для кого доступна возможность делать этот
    переход
    - ``permission_callback`` - опциональная функция для проверки возможности
    перехода.
    - ``enabled`` - используется для отключения определенных переходов

    Т.к. система не предусматривает прав для анонимных пользователей,
    для публичной доступности перехода необходимо указать значение
    ``Transition.ANONYMOUS_PERMISSION``.

    В случае, если список ``permissions`` пустой, переход автоматический,
    никому не доступен.

    В функцию ``permission_callback`` передаются аргументы: user, requestion,
    transition, request, form. Параметры user, request и form не обязательные::

        def perm_callback(requestion, transition, user=None, request=None,
                          form=None):
    """

    ANONYMOUS_PERMISSION = '*'

    def __init__(self, src, dst, transition, comment, permissions,
                 permission_callback=None, check_document=False, enabled=True):
        self.src = src
        self.dst = dst
        self.index = transition
        self.comment = comment
        self.required_permissions = permissions
        self.permission_cb = permission_callback
        self.confirmation_form_class = None
        self.check_document = check_document
        self.enabled = enabled


class Workflow(object):
    def __init__(self):
        self.transitions = []
        super(Workflow, self).__init__()

    def add(self, src, dst, transition, comment=u'', permissions=None,
            permission_callback=None, check_document=False, enabled=True):
        # проверим, что у нас нет повторяющихся id переходов
        if permissions is None:
            permissions = []
        if [tr for tr in self.transitions if tr.index == transition]:
            raise AttributeError(
                'Transition with id=%d already added' % transition)
        self.transitions.append(
            Transition(src, dst, transition, comment, permissions,
                       permission_callback, check_document, enabled))

    def available_transition_statuses(self, src):
        u"""
        Возвращает коды статусов, в которые можно перейти из указанного
        """
        transitions = filter(lambda t: t.src == src, self.transitions)
        return [t.dst for t in transitions if t.enabled]

    def available_transitions(self, src=None, dst=None):
        u"""
        Возвращает коды возможных переходов изменения статуса
        """
        transitions = self.transitions
        if src is not None and dst is not None:
            transitions = filter(
                lambda t: t.src == src and t.dst == dst, self.transitions)
        elif src is not None:
            transitions = filter(lambda t: t.src == src, self.transitions)
        elif dst is not None:
            transitions = filter(lambda t: t.dst == dst, transitions)
        return [t.index for t in transitions if t.enabled]

    def get_transition_by_index(self, index):
        transitions = filter(lambda t: t.index == index, self.transitions)
        if transitions:
            return transitions[0]
        else:
            return None

# Изменение статуса заявки()
REQUESTION_REGISTRATION_BY_OPERATOR = 0  # Регистрация через оператора
REQUESTION_IMPORT = 1                   # Импорт заявки
REQUESTION_ADD_BY_REQUESTER = 2         # Добавление заявки пользователем
CONFIRM_REQUESTION = 3                  # Документальное подтверждение заявки
ON_DISTRIBUTION = 5                     # Переход в комплектование
DECISION = 6                            # Выделено место
ON_DISTRIBUTION_RETURN = 7              # возврат в очередь нераспределенных
IMMEDIATELY_DECISION = 8                # Выделено место(немедленное зачисление)
REQUESTER_DECISION_BY_RESOLUTION = 9    # Выделено место по резолюции
ON_TEMP_DISTRIBUTION = 12               # Переход в комплектование временно зачисленной заявки
ON_TEMP_DISTRIBUTION_RETURN = 58        # Возврат в очередь нераспределенной временно зач-й
PERMANENT_DECISION = 13                 # Выделение места временно зачисленному
IMMEDIATELY_PERMANENT_DECISION = 14     # Выделение места временно зачисленному(немедленное зач-е)
DECISION_DISTRIBUTION = 16              # Зачислен
DECISION_ABSENT = 17                    # Невозможно установить контакт
DECISION_NOT_APPEAR = 18                # Неявка в ДОУ
ABSENT_DISTRIBUTED = 19                 # Явка в допольнительное время
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
DISTRIBUTION_BY_RESOLUTION = 58
# actions with id 59, 60 already taken
ES_DISTRIBUTION = 61                    # Зачислен через ЭлектроСад
# отказ от зачилсения на постоянной основе
DECISION_TEMP_DISTRIBUTED = 62      # Отказ от места в ДОУ
NOT_APPEAR_TEMP_DISTRIBUTED = 63    # Отказ от места в ДОУ после неявки
ABSENT_TEMP_DISTRIBUTED = 64        # Отказ от места в ДОУ после невозожности связаться
REQUESTION_TRANSFER = 66            # Перевод из другого муниципалитета
DISTRIBUTED_REQUESTER = 67          # Возврат в очередь после посещения ДОУ
DISTRIBUTED_ES_REQUESTER = 68       # Возврат в очередь после посещения ДОУ
DISTRIBUTED_KG_LEAVE = 69           # Выпуск из ДОУ
DISTRIBUTED_ES_KG_LEAVE = 70        # Выпуск из ДОУ

# Изменение данных заявки
CHANGE_REQUESTION = 71
CHANGE_REQUESTION_BY_OPERATOR = 72
CHANGE_ADMISSION_DATE = 73
CHANGE_ADMISSION_DATE_BY_OPERATOR = 74
CHANGE_PROFILE = 75
CHANGE_PROFILE_BY_OPERATOR = 76
CHANGE_REGISTRATION_DATETIME = 79
CHANGE_BIRTHDATE = 80
CHANGE_DOCUMENTS_BY_OPERATOR = 84 # используется при указании документа для заявки оператором
CREATE_PROFILE = 85
CREATE_PROFILE_BY_OPERATOR = 86
IMPORT_PROFILE = 87
EMBED_REQUESTION_TO_PROFILE = 88
CHANGE_REQUESTION_LOCATION = 89
ACCOUNT_CHANGE_REQUESTION = 90


# Распределение
DISTRIBUTION_INIT = 100
DISTRIBUTION_AUTO = 103
DISTRIBUTION_START = 101
DISTRIBUTION_END = 102

# Изменение данных ДОУ
CHANGE_SADIK_GROUP_PLACES = 104
CHANGE_SADIK_INFO = 105

# изменение путевки
VACANCY_DISTRIBUTED = 110

START_NEW_YEAR = 106

# устаревшие статусы, сохраняются для совместимости
CHANGE_PREFERRED_SADIKS = 77
CHANGE_PREFERRED_SADIKS_BY_OPERATOR = 78
CHANGE_BENEFITS = 81
CHANGE_BENEFITS_BY_OPERATOR = 82
CHANGE_DOCUMENTS = 83

# изменение персональных данных
CHANGE_PERSONAL_DATA = 200
CHANGE_PERSONAL_DATA_BY_OPERATOR = 201
CHANGE_PDATA_REQUESTION = 202
CHANGE_PDATA_REQUESTION_BY_OPERATOR = 203
EMAIL_VERIFICATION = 204
# 205 реализуется в модуле pgu
# перемещение персональных данных из модуля personal_data в ядро
MIGRATE_USER_PERSONAL_DATA = 220
MIGRATE_CHILD_PERSONAL_DATA = 221

# переходы, связанные с группами кратковременного пребывания
REQUESTER_SHORT_STAY = 300  # отметка о посещении групп КП
SHORT_STAY_DISTRIBUTION = 301  # из временного пребывания в комплектование
SHORT_STAY_REQUESTER = 302  # возврат в очередники из группы КП
DISTRIBUTION_SHORT_STAY = 303  # возврат в группу КП после комплектования
SHORT_STAY_DECISION_BY_RESOLUTION = 304  # выделение места по пезолюции

# поддержка авторизации через ЕСИА
CREATE_PROFILE_BY_ESIA = 500
BIND_ESIA_ACCOUNT = 501
UNBIND_ESIA_ACCOUNT = 502
CHANGE_PERSONAL_DATA_BY_ESIA = 503

# эти логи будут отображаться в блоке 'Персональные данные'
PERSONAL_DATA_ACTION_FLAGS = (
    CHANGE_PERSONAL_DATA,
    CHANGE_PERSONAL_DATA_BY_OPERATOR,
    MIGRATE_USER_PERSONAL_DATA,
    CHANGE_PERSONAL_DATA_BY_ESIA,
)

# внетренние системные переходы, выполняются по упрощенной схеме
# недоступны пользователям, инициируются либо извне (по api), либо внутренними
# командами (по расписанию)
INNER_TRANSITIONS = [
    REQUESTER_SHORT_STAY,
    SHORT_STAY_REQUESTER,
]

workflow = Workflow()

# 1) Подача заявления
workflow.add(None, STATUS_REQUESTER_NOT_CONFIRMED, REQUESTION_ADD_BY_REQUESTER,
             u'Самостоятельная регистрация', )
workflow.add(None, STATUS_REQUESTER, REQUESTION_IMPORT, u'Импорт заявки')
workflow.add(None, STATUS_REQUESTER, REQUESTION_REGISTRATION_BY_OPERATOR,
             u'Регистрация через оператора', )
workflow.add(STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REQUESTER,
             CONFIRM_REQUESTION, u'Подтверждение заявки',
             permissions=[OPERATOR_PERMISSION[0]])
workflow.add(None, STATUS_REQUESTER, REQUESTION_TRANSFER,
             u'Перевод из другого муниципалитета',)

# 2) Комплектование
# 2.1) Очередники
workflow.add(STATUS_REQUESTER, STATUS_ON_DISTRIBUTION, ON_DISTRIBUTION,
             u'Перевод в комплектование')
workflow.add(STATUS_SHORT_STAY, STATUS_ON_DISTRIBUTION, SHORT_STAY_DISTRIBUTION,
             u'Перевод из временного пребывания в комплектование')
workflow.add(STATUS_ON_DISTRIBUTION, STATUS_DECISION, DECISION,
             u'Выделение места в ДОУ')
workflow.add(STATUS_REQUESTER, STATUS_DECISION,
             REQUESTER_DECISION_BY_RESOLUTION,
             u'Выделение места в ДОУ по резолюции начальника',
             permissions=[SUPERVISOR_PERMISSION[0]], check_document=True)
workflow.add(STATUS_SHORT_STAY, STATUS_DECISION,
             SHORT_STAY_DECISION_BY_RESOLUTION,
             u'Выделение места в ДОУ по резолюции начальника',
             permissions=[SUPERVISOR_PERMISSION[0]], check_document=True)
workflow.add(STATUS_ON_DISTRIBUTION, STATUS_REQUESTER, ON_DISTRIBUTION_RETURN,
             u'Возврат в очередь нераспределенных')
workflow.add(STATUS_ON_DISTRIBUTION, STATUS_SHORT_STAY, DISTRIBUTION_SHORT_STAY,
             u'Возврат в группы КП нераспределенных')
# Немедленное зачисление
if IMMEDIATELY_DISTRIBUTION != IMMEDIATELY_DISTRIBUTION_NO:
    workflow.add(STATUS_REQUESTER, STATUS_DECISION, IMMEDIATELY_DECISION,
                 u'Выделение места в ДОУ (немедленное зачисление)',
                 permissions=[DISTRIBUTOR_PERMISSION[0]])


# 2.3) Временное зачисление
if TEMP_DISTRIBUTION == TEMP_DISTRIBUTION_YES:
    workflow.add(STATUS_TEMP_DISTRIBUTED, STATUS_ON_TEMP_DISTRIBUTION,
                 ON_TEMP_DISTRIBUTION,
                 u'Комплектование временно зачисленных')
    workflow.add(STATUS_ON_TEMP_DISTRIBUTION, STATUS_TEMP_DISTRIBUTED,
                 ON_TEMP_DISTRIBUTION_RETURN,
                 u'Возврат нераспределенных в очередь(временно зачисленные)')
    workflow.add(STATUS_ON_TEMP_DISTRIBUTION, STATUS_DECISION,
                 PERMANENT_DECISION,
                 u'Выделение места в ДОУ на постоянное основе')
    # Немедленное зачисление
    if IMMEDIATELY_DISTRIBUTION != IMMEDIATELY_DISTRIBUTION_NO:
        workflow.add(
            STATUS_TEMP_DISTRIBUTED, STATUS_DECISION,
            IMMEDIATELY_PERMANENT_DECISION,
            u'Выделение места в ДОУ на постоянной основе(немедленное зачисление)',
            permissions=[DISTRIBUTOR_PERMISSION[0]])


# 3) Зачисление
# 3.1) Очередники
# переход с обычным зачислением остается для обратной совместимости с ранее
# зачисленными заявками, запрет на это действие накладывается через метод у
# объекта заявки requestion.is_available_for_actions
workflow.add(STATUS_DECISION, STATUS_DISTRIBUTED, DECISION_DISTRIBUTION,
             u'Зачисление', permissions=[DISTRIBUTOR_PERMISSION[0]],
             check_document=True)
workflow.add(STATUS_DECISION, STATUS_DISTRIBUTED_FROM_ES, ES_DISTRIBUTION,
             u'Зачисление через систему ЭлектроСад', check_document=True)
# workflow.add(STATUS_REQUESTER, STATUS_DISTRIBUTED, DISTRIBUTION_BY_RESOLUTION,
#              u'Зачисление по резолюции Начальника',
#              permissions=[SUPERVISOR_PERMISSION[0]], check_document=True)
# workflow.add(STATUS_DECISION, STATUS_ABSENT, DECISION_ABSENT,
#              u'Невозможно установить контакт с заявителем',
#              permissions=[DISTRIBUTOR_PERMISSION[0]])
workflow.add(STATUS_DECISION, STATUS_NOT_APPEAR, DECISION_NOT_APPEAR,
             u'Неявка в ДОУ', permissions=[DISTRIBUTOR_PERMISSION[0]])
workflow.add(STATUS_ABSENT, STATUS_DISTRIBUTED, ABSENT_DISTRIBUTED,
             u'Явка в дополнительное время отсутствующих',
             permissions=[DISTRIBUTOR_PERMISSION[0]], check_document=True)
# Путевки
if ETICKET != ETICKET_NO:
    workflow.add(STATUS_DECISION, STATUS_PASS_GRANTED, PASS_GRANTED,
                 u'Получение путевки', permissions=[DISTRIBUTOR_PERMISSION[0]])
    workflow.add(STATUS_PASS_GRANTED, STATUS_DISTRIBUTED, PASS_DISTRIBUTED,
                 u'Зачисление по путевке',
                 permissions=[DISTRIBUTOR_PERMISSION[0]])
    workflow.add(STATUS_PASS_GRANTED, STATUS_NOT_APPEAR, PASS_NOT_APPEAR,
                 u'Неявка в ДОУ с путевкой',
                 permissions=[DISTRIBUTOR_PERMISSION[0]])

# 3.3) Временное зачисление
if TEMP_DISTRIBUTION == TEMP_DISTRIBUTION_YES:
#    зачисление на постоянной основе
#    временное зачисление
    workflow.add(STATUS_REQUESTER, STATUS_TEMP_DISTRIBUTED,
                 TEMP_DISTRIBUTION_TRANSFER, u'Временное зачисление',
                 permissions=[DISTRIBUTOR_PERMISSION[0]])
    # Путевки для временного зачисления
    if ETICKET != ETICKET_NO:
        workflow.add(STATUS_REQUESTER, STATUS_TEMP_PASS_TRANSFER,
                     TEMP_PASS_TRANSFER, u'Выдача временной путевки',
                     permissions=[DISTRIBUTOR_PERMISSION[0]])
        workflow.add(STATUS_TEMP_PASS_TRANSFER, STATUS_TEMP_DISTRIBUTED,
                     TEMP_PASS_DISTRIBUTION, u'Временное зачисление по путевке',
                     permissions=[DISTRIBUTOR_PERMISSION[0]])

# 4) Отказы

workflow.add(STATUS_REQUESTER, STATUS_REMOVE_REGISTRATION,
             REQUESTER_REMOVE_REGISTRATION, u'Снятие с учёта',
             permissions=[OPERATOR_PERMISSION[0]])
workflow.add(STATUS_REMOVE_REGISTRATION, STATUS_REQUESTER,
             RESTORE_REQUESTION, u'Восстановление в очереди',
             permissions=[SUPERVISOR_PERMISSION[0]],
             check_document=True)
workflow.add(STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REMOVE_REGISTRATION,
             NOT_CONFIRMED_REMOVE_REGISTRATION, u'Отклонение заявки',
             permissions=[OPERATOR_PERMISSION[0]])
workflow.add(STATUS_ABSENT, STATUS_ABSENT_EXPIRE, ABSENT_EXPIRE,
             u'Истечение сроков на обжалование отсутствия')
workflow.add(STATUS_ABSENT_EXPIRE, STATUS_REMOVE_REGISTRATION,
             ABSENT_REMOVE_REGISTRATION,
             u'Снятие с учёта по истечению срока на установление контакта',
             permissions=[OPERATOR_PERMISSION[0]])

workflow.add(STATUS_REMOVE_REGISTRATION, STATUS_ARCHIVE,
             REMOVE_REGISTRATION_ARCHIVE, u'Архивация снятых с учёта')
workflow.add(STATUS_DISTRIBUTED, STATUS_ARCHIVE, DISTRIBUTED_ARCHIVE,
             u'Архивация зачисленных')

workflow.add(STATUS_DECISION, STATUS_REQUESTER, DECISION_REQUESTER,
             u'Отказ от места в ДОУ',
             permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]],
             check_document=True)
workflow.add(STATUS_NOT_APPEAR, STATUS_REQUESTER, NOT_APPEAR_REQUESTER,
             u'Восстановление в очереди после неявки',
             permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]],
             check_document=True)
workflow.add(STATUS_ABSENT, STATUS_REQUESTER, ABSENT_REQUESTER,
             u'Отказ от места в ДОУ после отсутствия',
             permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]],
             check_document=True)
workflow.add(STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REJECTED,
             REQUESTION_REJECT, u'Истечение сроков на подтверждение документов')

# транзакции не используются, но для сохранения корректного отображения в логах
# заявок, остаются в системе
workflow.add(STATUS_DISTRIBUTED, STATUS_REQUESTER,
             DISTRIBUTED_REQUESTER, u'Повторная постановка на учет',
             permissions=[SUPERVISOR_PERMISSION[0]], check_document=True,
             enabled=False)
workflow.add(STATUS_DISTRIBUTED_FROM_ES, STATUS_REQUESTER,
             DISTRIBUTED_ES_REQUESTER, u'Повторная постановка на учет',
             permissions=[SUPERVISOR_PERMISSION[0]], check_document=True,
             enabled=False)


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
                 u'Возврат путевки',
                 permissions=[OPERATOR_PERMISSION[0], REQUESTER_PERMISSION[0]])

# Временное зачисление
if TEMP_DISTRIBUTION == TEMP_DISTRIBUTION_YES:
    workflow.add(STATUS_DISTRIBUTED, STATUS_TEMP_ABSENT, TEMP_ABSENT,
                 u"Длительное отсутствие по уважительной причине",
                 permissions=[OPERATOR_PERMISSION[0]])
    workflow.add(STATUS_TEMP_ABSENT, STATUS_DISTRIBUTED, TEMP_ABSENT_CANCEL,
                 u"Возврат после отсутствия по уважительной причине",
                 permissions=[OPERATOR_PERMISSION[0]])
    workflow.add(STATUS_TEMP_DISTRIBUTED, STATUS_REQUESTER,
                 RETURN_TEMP_DISTRIBUTED,
                 u'Возвращение в очередь из временно зачисленных',
                 permissions=[OPERATOR_PERMISSION[0]])
    # Путевки
    if ETICKET != ETICKET_NO:
        workflow.add(STATUS_TEMP_PASS_TRANSFER, STATUS_REQUESTER,
                     RETURN_TEMP_PASS_TRANSFER, u'Возврат временной путевки',
                     permissions=[OPERATOR_PERMISSION[0]])

# 5. Посещение групп кратковременного пребывания
workflow.add(STATUS_REQUESTER, STATUS_SHORT_STAY, REQUESTER_SHORT_STAY,
             u'Перевод в группу кратковременного пребывания')
workflow.add(STATUS_SHORT_STAY, STATUS_REQUESTER, SHORT_STAY_REQUESTER,
             u'Перевод из группы кратковременного пребывания в очередь')

# повторная регистрация после выпуска из ДОУ
workflow.add(STATUS_DISTRIBUTED_FROM_ES, STATUS_KG_LEAVE,
             DISTRIBUTED_ES_KG_LEAVE, u"Выпуск из ДОУ")
workflow.add(STATUS_DISTRIBUTED, STATUS_KG_LEAVE, DISTRIBUTED_KG_LEAVE,
             u"Выпуск из ДОУ")

DISABLE_EMAIL_ACTIONS = [
    DECISION, PERMANENT_DECISION,
    MIGRATE_USER_PERSONAL_DATA, MIGRATE_CHILD_PERSONAL_DATA,
]

STATUS_CHANGE_TRANSITIONS = [transition.index for transition in workflow.transitions]

ACTION_CHOICES = [(transition.index, transition.comment) for transition in
                  workflow.transitions]

ACTION_CHOICES.extend(
    #    добавляем действия с заявками
    [(CHANGE_REQUESTION, u"Изменение заявки пользователем"), # старый статус(отдельно от изменения ДОУ и льгот)
     (ACCOUNT_CHANGE_REQUESTION, u"Изменение заявки пользователем"), # также изменяются льготы и ДОУ
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
     (CHANGE_REQUESTION_LOCATION,
      u"Изменение местоположения заявки во время распределения"),

     # Удаленные статусы
     (NOT_APPEAR_REMOVE_REGISTRATION, u"Снятие с учета по причине неявки"),
     (NOT_APPEAR_EXPIRE, u"Истечение сроков обжалования"),
     (DISTRIBUTION_BY_RESOLUTION, u"Зачисление по резолюции Начальника"),

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
     # персональные данные
     (CHANGE_PERSONAL_DATA, u'Изменение персональных данных пользователем'),
     (CHANGE_PERSONAL_DATA_BY_OPERATOR, u'Изменение персональных данных оператором'),
     (CHANGE_PDATA_REQUESTION, u'Изменение персональных данных заявки пользователем'),
     (CHANGE_PDATA_REQUESTION_BY_OPERATOR, u'Изменение персональных данных заявки оператором'),
     (EMAIL_VERIFICATION, u'Подтверждение почтового ящика'),
     (MIGRATE_USER_PERSONAL_DATA,
        u'Перенос персональных данных пользователя в связи с обновлением до v1.9'),
     (MIGRATE_CHILD_PERSONAL_DATA,
        u'Перенос персональных данных ребёнка в связи с обновлением до v1.9'),
     (CREATE_PROFILE_BY_ESIA,
        u'Создание нового профиля при регистрации через ЕСИА'),
     (BIND_ESIA_ACCOUNT, u'Связывание профиля с аккаунтом ЕСИА'),
     (UNBIND_ESIA_ACCOUNT, u'Разрыв связи профиля с аккаунтом ЕСИА'),
     (CHANGE_PERSONAL_DATA_BY_ESIA,
        u'Изменение перс. данных пользователя при авторизации через ЕСИА'),
    ]
)

ACTION_TEMPLATES = dict(
    [(transition.index, {ANONYM_LOG: Template(u"")})
     for transition in workflow.transitions]
)

# ----------------------------------
# Шаблоны для записи логов
#
# В контекст можно передавать changed_data и cleaned_data из формы
# также в шаблон передается заявка для которой происходит сохранение логов под именем requestion
# (удобно получать занчение полей через get_FOO_display)
# 
# {% if "field_name" in changed_data %}
#     {{ cleaned_data.field_name }} {{ requestion.get_field_name_display }}
# {% endif %}
# ------------------------------------

#переопределеяем стандартные шаблоны для действий с заявкой

document_confirmation_template = u"""
        {% if other_requestions %}
            Заявки с таким же идентифицирующим документом были сняты с учета:
            {% for requestion in other_requestions %}
                {{ requestion }}{% if not forloop.last %}; {% endif %}
            {% endfor %}
        {% endif %}
        """

ACTION_TEMPLATES.update({
    NOT_CONFIRMED_REMOVE_REGISTRATION: {
        ANONYM_LOG: Template(u""),
        OPERATOR_LOG: Template(
            u"""Заявка {{ other_requestion }} с таким же идентифицирующим документом была документально подтверждена"""),
    },
    CONFIRM_REQUESTION: {
        ANONYM_LOG: Template(u""),
        OPERATOR_LOG: Template(document_confirmation_template),
    },
    RESTORE_REQUESTION: {
        ANONYM_LOG: Template(u""),
        OPERATOR_LOG: Template(document_confirmation_template),
    },
})

requestion_account_template = u"""
    {% if requestion.sex %}Пол: {{ requestion.get_sex_display }};{% endif %}
    {% if requestion.child_last_name %}Фамилия: {{ requestion.child_last_name }};{% endif %}
    {% if requestion.name %}Имя: {{ requestion.name }};{% endif %}
    {% if requestion.child_middle_name %}Отчество: {{ requestion.child_middle_name }};{% endif %}
    {% if requestion.birthplace %}Место рождения: {{ requestion.birthplace }};{% endif %}
    {% if requestion.kinship %}Заявитель: {{ requestion.kinship }};{% endif %}
    {% if requestion.comment %}Комментарий: {{ requestion.comment }};{% endif %}
    {% if requestion.template %}Тип документа: {{ requestion.template }};{% endif %}
    {% if requestion.document_number %}Номер документа: {{ requestion.document_number }};{% endif %}
    {% if requestion.location %}Местоположение: {{ requestion.location.x }}, {{ requestion.location.y }};{% endif %}
    {% if requestion.child_snils %}СНИЛС: {{ requestion.child_snils }};{% endif %}
    {% if benefit_documents %}
        Документы для льгот:
        {% for document in benefit_documents %}
            {{ document.template }}: {{ document.document_number }}{% if not forloop.last %},{% else %};{% endif %}
        {% endfor %}
    {% endif %}
    """

requestion_anonym_template = u"""
    Группы ДОУ:
    {% for area in areas %}
        {{ area }};
    {% empty %}
        Весь муниципалитет;
    {% endfor %}
    {% if requestion.birth_date %}Дата рождения: {{ requestion.birth_date }};{% endif %}
    {% if not requestion.distribute_in_any_sadik == None %}Зачислять в любой ДОУ: {{ requestion.distribute_in_any_sadik|yesno:"Да, Нет" }};{% endif %}
    {% if requestion.admission_date %}Желаемая дата зачисления: {{ requestion.admission_date }};{% endif %}
    {% if pref_sadiks %}
        Приоритетные МДОУ: {% for sadik in pref_sadiks %}{{ sadik }};{% endfor %}
    {% endif %}
    """

registration_account_template = u"""
    {% if user.email %}Электронная почта:{{ user.email }}{% endif %}
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
    {% if "phone_number" in changed_data %}Телефон: {{ profile.phone_number }};{% endif %}
    {% if "mobile_number" in changed_data %}Мобильный телефон: {{ profile.mobile_number }};{% endif %}
    '''

change_requestion_anonym_template = u"""
        {% if "admission_date" in changed_data %}Желаемая дата зачисления: {{ requestion.admission_date }};{% endif %}
        {% if "benefits" in changed_data %}
            Основная категория льгот: {{ requestion.benefit_category }};
        {% endif %}
        {% if "areas" in changed_data %}
            Группы ДОУ:
            {% for area in cleaned_data.areas %}
                {{ area }};
            {% empty %}
                Весь муниципалитет;
            {% endfor %}
        {% endif %}
        {% if "pref_sadiks" in changed_data %}
            Приоритетные МДОУ: {% for sadik in cleaned_data.pref_sadiks %}{{ sadik }}; {% endfor %}
        {% endif %}
        {% if "distribute_in_any_sadik" in changed_data %}Зачислять в любой ДОУ: {{ cleaned_data.distribute_in_any_sadik|yesno:"да,нет" }};{% endif %}
        {% if "district" in changed_data %} Район: {{ requestion.district }};{% endif %} 
        """

change_requestion_account_template = u"""
        {% if "sex" in changed_data %}Пол: {{ requestion.get_sex_display }};{% endif %}
        {% if "child_last_name" in changed_data %}Фамилия: {{ requestion.child_last_name }};{% endif %}
        {% if "name" in changed_data %}Имя: {{ requestion.name }};{% endif %}
        {% if "child_middle_name" in changed_data %}Отчество: {{ requestion.child_middle_name }};{% endif %}
        {% if "birthplace" in changed_data %}Место рождения: {{ requestion.birthplace }};{% endif %}
        {% if "kinship" in changed_data %}Заявитель: {{ requestion.kinship }};{% endif %}
        {% if "comment" in changed_data %}Комментарий: {{ requestion.comment }};{% endif %}
        {% if "location" in changed_data %}Местоположение: {{ requestion.location.x }}, {{ requestion.location.y }};{% endif %}
        {% if "child_snils" in changed_data %}СНИЛС: {{ requestion.child_snils }};{% endif %}
        {% if "benefits" in changed_data %}
            {% if cleaned_data.benefits %}
                Льготы: {% for benefit in cleaned_data.benefits %}{{ benefit }}; {% endfor %}
            {% endif %}
        {% endif %}
        {% with profile.get_identity_documents as document %}
        {% if "benefit_documents" in cleaned_data %}
            {% if cleaned_data.benefit_documents %}
                Документы для льгот:
                {% for document in cleaned_data.benefit_documents %}
                    {{ document.template }}: {{ document.document_number }}{% if not forloop.last %},{% else %};{% endif %}
                {% endfor %}
            {% else %}
                Документы для льгот не заданы;
            {% endif %}
        {% endif %}
    {% endwith %}
        """

change_preferred_sadiks_anonym_template = u'''
    {% if "areas" in changed_data %}
        Группы ДОУ:
        {% for area in cleaned_data.areas %}
            {{ area }};
        {% empty %}
            Весь муниципалитет;
        {% endfor %}
    {% endif %}
    {% if "pref_sadiks" in changed_data %}
        Приоритетные МДОУ: {% for sadik in cleaned_data.pref_sadiks %}{{ sadik }}; {% endfor %}
    {% endif %}
    {% if "distribute_in_any_sadik" in changed_data %}Зачислять в любой ДОУ: {{ cleaned_data.distribute_in_any_sadik|yesno:"да,нет" }};{% endif %}
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
    {% if requestion_documents %}
        Документы:
        {% for document in requestion_documents %}
            {{ document.document_number }} ({{ document.template }});
        {% endfor %}.
    {% endif %}
    """

decision_distribution_anonym = u"""Было завершено зачисление в {{ sadik }}"""
es_decision_distribution_anonym = u"""
    По решению оператора {{ operator }} системы ЭлектроСад было завершено
    зачисление в {{ sadik|safe }}"""
decision_not_appear_anonym = u"""
    Заявитель не явился в назначенный срок для зачисления в {{ sadik|safe }}
    {% if operator %}. Неявку отметил оператор ЭлектроСада
    {{ operator }}.{% endif %}"""
decision_requster_anonym = u"""
    Заявитель отказался от выделенного места в {{ sadik|safe }}.
    Заявка была возвращена в очередь. {% if operator %}
    Процедуру возврата инициировал оператор ЭлектроСада {{ operator }}.
    {% endif %}"""

email_verification_template = u"Почтовый адрес {{ email }} успешно подтвержден."

requester_short_stay = u"""
    Ребенок посещает группу кратковременного пребывания в {{ sadik|safe }}.
    {% if operator %} Добавил ребенка в группу оператор ЭлектроСада
    {{ operator }}.{% endif %}"""

short_stay_requester = u"""
    Ребенок выпущен из группы кратковременного пребывания в {{ sadik|safe }}.
    {% if operator %} Процедуру провел оператор ЭлектроСада {{ operator }}.
    {% endif %}"""

decision_by_resolution_anonym = u"""
    Выделено место в {{ sadik|safe }}. Должность резолюционера:
    {{ resolutioner_post }}. ФИО резолюционера: {{ resolutioner_fio }}.
    Номер документа: {{ resolution_number }}."""

distributed_requester_template = u"""
    Заявка повторно поставлена на учет. Новая дата постановки в очередь:
    {{ requestion.registration_datetime }}.
    Статус: {{ requestion.get_status_display }}
    """

distributed_kg_leave_template = u"""
    Ребенок был выпущен из ДОУ оператором {{ operator }}.
    """

change_pdata_field_template = u"""
    {% if old_value %}
        {% if new_value %}
            {% if old_value != new_value %}
                {{ field_name }}: с {{ old_value }} на {{ new_value }};
            {% endif %}
        {% else %}
            {{ field_name }}: удалено, было {{ old_value }});
        {% endif %}
    {% elif new_value %}
        {{ field_name }}: {{ new_value }};
    {% endif %}
    """

change_personal_data_template = u"""
    {{% with field_name='Фамилия' old_value=old_pdata.last_name new_value=new_pdata.last_name %}}
        {change_field_template}
    {{% endwith %}}
    {{% with field_name='Имя' old_value=old_pdata.first_name new_value=new_pdata.first_name %}}
        {change_field_template}
    {{% endwith %}}
    {{% with field_name='Отчество' old_value=old_pdata.middle_name new_value=new_pdata.middle_name %}}
        {change_field_template}
    {{% endwith %}}
    {{% with field_name='Телефон' old_value=old_pdata.phone_number new_value=new_pdata.phone_number %}}
        {change_field_template}
    {{% endwith %}}
    {{% with field_name='Дополнительный телефон' old_value=old_pdata.mobile_number new_value=new_pdata.mobile_number %}}
        {change_field_template}
    {{% endwith %}}
    {{% with field_name='СНИЛС' old_value=old_pdata.snils new_value=new_pdata.snils %}}
        {change_field_template}
    {{% endwith %}}
    {{% with field_name='Населённый пункт' old_value=old_pdata.town new_value=new_pdata.town %}}
        {change_field_template}
    {{% endwith %}}
    {{% with field_name='Улица' old_value=old_pdata.street new_value=new_pdata.street %}}
        {change_field_template}
    {{% endwith %}}
    {{% with field_name='Номер дома' old_value=old_pdata.house new_value=new_pdata.house %}}
        {change_field_template}
    {{% endwith %}}
    {{% if old_pdata.personal_documents %}}
        {{% if new_pdata.personal_documents.0 != old_pdata.personal_documents.0 %}}
            Документы: c {{{{ old_pdata.personal_documents.0 }}}} на {{{{ new_pdata.personal_documents.0 }}}}.
        {{% endif %}}
    {{% else %}}
        Документы: {{{{ new_pdata.personal_documents.0 }}}}.
    {{% endif %}}
    """.format(change_field_template=change_pdata_field_template)

migrate_personal_data_template = u"""
    {% for field_name, field_value in new_data.items %}
        {{ field_name }}: {{ field_value }};
    {% endfor %}
    """

bind_esia_account_template = u"""
    Профиль: {{ profile }}.
    {% if binding %}Привязана{% else %}Отвязана{% endif %}
    учётная запись ЕСИА №{{ esia_id }}.
    """


ACTION_TEMPLATES.update({
    REQUESTION_ADD_BY_REQUESTER: {
        ACCOUNT_LOG: Template(requestion_account_template + change_benefits_account_template),
        ANONYM_LOG: Template(requestion_anonym_template + change_benefits_anonym_template)
    },
    CREATE_PROFILE: {
        ACCOUNT_LOG: Template(registration_account_template),
    },
    CREATE_PROFILE_BY_OPERATOR: {
        ACCOUNT_LOG: Template(registration_account_template),
    },
    REQUESTION_REGISTRATION_BY_OPERATOR: {
        ACCOUNT_LOG: Template(requestion_account_template + change_benefits_account_template),
        ANONYM_LOG: Template(requestion_anonym_template + change_benefits_anonym_template),
    },
    IMPORT_PROFILE: {
        ACCOUNT_LOG: Template(registration_account_template),
    },
    REQUESTION_IMPORT: {
        ACCOUNT_LOG: Template(requestion_account_template + change_benefits_account_template),
        ANONYM_LOG: Template(requestion_anonym_template + change_benefits_anonym_template),
    },
    ACCOUNT_CHANGE_REQUESTION: {
        ANONYM_LOG: Template(change_requestion_anonym_template),
        ACCOUNT_LOG: Template(change_requestion_account_template),
    },
    CHANGE_REQUESTION_BY_OPERATOR: {
        ANONYM_LOG: Template(change_requestion_anonym_template),
        ACCOUNT_LOG: Template(change_requestion_account_template),
    },
    CHANGE_REQUESTION_LOCATION: {
        ACCOUNT_LOG: Template(u"""
            {% if "location" in changed_fields %}Местоположение: {{ requestion.location.x }}, {{ requestion.location.y }};{% endif %}
        """)
    },
    CHANGE_PROFILE: {
        ACCOUNT_LOG: Template(change_profile_account_template),
    },
    CHANGE_PROFILE_BY_OPERATOR: {
        ACCOUNT_LOG: Template(change_profile_account_template),
    },
    CHANGE_DOCUMENTS_BY_OPERATOR: {
        ACCOUNT_LOG: Template(change_documents_account_template),
    },
    DISTRIBUTION_INIT: {
        OPERATOR_LOG: Template(u'''Распеределение создано''')
    },
    DISTRIBUTION_START: {
        OPERATOR_LOG: Template(u'''Распеределение начато''')
    },
    DISTRIBUTION_END: {
        OPERATOR_LOG: Template(u'''Распеределение завершено''')
    },
    CHANGE_REGISTRATION_DATETIME: {
        ANONYM_LOG: Template(u"""Дата регистрации изменена на {{ registration_datetime }}""")
    },
    CHANGE_BIRTHDATE: {
        ANONYM_LOG: Template(u"""Дата рождения изменена на {{ birth_date }}""")
    },
    CHANGE_SADIK_GROUP_PLACES: {
        ANONYM_LOG: Template(u"""Свободных мест:{{ sadik_group.free_places }}; Всего мест:{{ sadik_group.capacity }}""")
    },
    CHANGE_SADIK_INFO: {
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
    },
    DECISION_DISTRIBUTION: {
        ANONYM_LOG: Template(decision_distribution_anonym)
    },
    ES_DISTRIBUTION: {
        ANONYM_LOG: Template(es_decision_distribution_anonym)
    },
    DECISION_REQUESTER: {
        ANONYM_LOG: Template(decision_requster_anonym)
    },
    NOT_APPEAR_REQUESTER: {
        ANONYM_LOG: Template(decision_requster_anonym)
    },
    DECISION_NOT_APPEAR: {
        ANONYM_LOG: Template(decision_not_appear_anonym)
    },
    DECISION: {
        ANONYM_LOG: Template(u"""Было выделено место в {{ sadik }}""")
    },
    REQUESTER_DECISION_BY_RESOLUTION: {
        ANONYM_LOG: Template(decision_by_resolution_anonym)
    },
    EMAIL_VERIFICATION: {
        ACCOUNT_LOG: Template(email_verification_template)
    },
    REQUESTION_TRANSFER: {
        ANONYM_LOG: Template(u"""
        Заявка перенесена из другого муниципалитета: {{ sender_info }}.
        """)
    },
    REQUESTER_SHORT_STAY: {
        ANONYM_LOG: Template(requester_short_stay)
    },
    SHORT_STAY_REQUESTER: {
        ANONYM_LOG: Template(short_stay_requester)
    },
    SHORT_STAY_DECISION_BY_RESOLUTION: {
        ANONYM_LOG: Template(decision_by_resolution_anonym)
    },
    DISTRIBUTED_REQUESTER: {
        ANONYM_LOG: Template(distributed_requester_template)
    },
    DISTRIBUTED_ES_REQUESTER: {
        ANONYM_LOG: Template(distributed_requester_template)
    },
    DISTRIBUTED_ES_KG_LEAVE: {
        ANONYM_LOG: Template(distributed_kg_leave_template)
    },
    DISTRIBUTED_KG_LEAVE: {
        ANONYM_LOG: Template(distributed_kg_leave_template)
    },
    CHANGE_PERSONAL_DATA: {
        ACCOUNT_LOG: Template(change_personal_data_template)
    },
    CHANGE_PERSONAL_DATA_BY_OPERATOR: {
        ACCOUNT_LOG: Template(change_personal_data_template)
    },
    MIGRATE_USER_PERSONAL_DATA: {
        ACCOUNT_LOG: Template(migrate_personal_data_template)
    },
    MIGRATE_CHILD_PERSONAL_DATA: {
        ACCOUNT_LOG: Template(migrate_personal_data_template)
    },
    BIND_ESIA_ACCOUNT: {
        OPERATOR_LOG: Template(bind_esia_account_template)
    },
    UNBIND_ESIA_ACCOUNT: {
        OPERATOR_LOG: Template(bind_esia_account_template)
    },
    CHANGE_PERSONAL_DATA_BY_ESIA: {
        ACCOUNT_LOG: Template(change_personal_data_template)
    },
})


def extend_action_choices(extension_data):
    """

    @type extension_data: list
    """
    if not isinstance(extension_data, list):
        raise AttributeError(u'Attribute extension_data must be list of tuples')

    existing_indices = [key for key, value in ACTION_CHOICES]

    for element in extension_data:
        if not isinstance(element, tuple) or len(element) != 2:
            raise AttributeError(u'Elements of extension_data must be tuples with length is equal 2')

        if not isinstance(element[0], int):
            raise AttributeError(u'First element of extension_data tuple must be integer')

        if not isinstance(element[1], (str, unicode)):
            raise AttributeError(u'Second element of extension_data tuple must be string or unicode')

        if element[0] in existing_indices:
            raise AttributeError(u'Action choice with index %d already exist' % element[0])

    ACTION_CHOICES.extend(extension_data)


def extend_action_templates(extension_data):
    """

    @type extension_data: dict
    """
    if not isinstance(extension_data, dict):
        raise AttributeError(u'Attribute extension_data must be dict')

    existing_indices = [key for key, value in ACTION_TEMPLATES.iteritems()]

    for index, templates in extension_data.iteritems():
        if not isinstance(index, int):
            raise AttributeError(u'Key of extension_data dict must be integer')

        if not isinstance(templates, dict):
            raise AttributeError(u'Value of extension_data dict must be dict')

        if index in existing_indices:
            raise AttributeError(u'Action choice with index %d already exist' % index)

        for level, template in templates.iteritems():
            if level not in [ANONYM_LOG, ACCOUNT_LOG, OPERATOR_LOG]:
                raise AttributeError(
                    u'Key of extension_data value dict must be ANONYM_LOG or ACCOUNT_LOG or OPERATOR_LOG')

            if not isinstance(template, Template):
                raise AttributeError(u'Value of extension data value dict must instance of Template class')

    ACTION_TEMPLATES.update(extension_data)
