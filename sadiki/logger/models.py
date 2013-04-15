# -*- coding: utf-8 -*-
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.query_utils import Q
from django.template.context import Context
from django.template.loader import render_to_string
from sadiki.core.models import query_set_factory, Requestion, \
    DISTRIBUTION_TYPE_CHOICES
from sadiki.core.utils import scheme_and_domain
import json
import logging
import re


class LoggerManager(models.Manager):
    def create_for_action(self, action_flag, context_dict=None, extra=None, reason=None):
        u"""
        создается запись в логах + создаются сообщения для всех уровней
        логирования(основываясь на шаблонах ACTION_TEMPLATES)

        Аргументы:
        action_flag - тип действия, записанный в workflow
        context_dict - контекст, передающийся в шаблон
        extra - дополнительные параметры:
            user - пользователь выполнивший действие
            sadik_group - группа ДОУ по отношению к которой выполнеяется действие,
                        например распределение заявки
            age_group - возрастная группа
            added_pref_sadiks - ДОУ, которые были добавлены
            removed_pref_sadiks - ДОУ, которые были удалены
        """
        from sadiki.core.workflow import DISABLE_EMAIL_ACTIONS
        from sadiki.core.workflow import ACTION_TEMPLATES
        context = Context(context_dict)
        if extra is None:
            extra = {}
        obj = extra.get('obj')
        log = Logger(
                reason=reason,
                action_flag=action_flag,
                content_object=obj,
                user=extra.get('user')
            )
#        к логу добавляем дополнительную информацию
        if isinstance(obj, Requestion):
            if obj.distributed_in_vacancy:
                log.vacancy = obj.distributed_in_vacancy
#                надо сохранить возрастную группу, т.к. может изменяться у группы в ДОУ
                age_groups = (obj.distributed_in_vacancy.sadik_group.age_group,)
            else:
                age_groups = obj.age_groups()
            if 'profile' in extra:
                log.profile = extra['profile']
            if 'distribution_type' in extra:
                log.distribution_type = extra['distribution_type']
#            need save instance before work with many to many(pk required)
            log.save()
            if age_groups:
                log.age_groups = age_groups
            if 'added_pref_sadiks' in extra:
                log.added_pref_sadiks = extra['added_pref_sadiks']
            if 'removed_pref_sadiks' in extra:
                log.removed_pref_sadiks = extra['removed_pref_sadiks']

        else:
            log.save()
            if 'age_group' in extra:
                log.age_groups = (extra['age_group'],)
            #        для данного типа изменений создаем сообщения в логах для всех
#        уровней логирования
        main_message = u''
        if action_flag in ACTION_TEMPLATES:
            for log_level, template  in ACTION_TEMPLATES[action_flag].iteritems():
                message = template.render(context).strip()
    #            убираем лишние пробелы
                message = re.sub(r"\s+", u" ", message)
    #            если текстового сообщения нет(например не изменялись публичные поля)
    #            то не сохраняем
                if message:
                    main_message = u"%s %s" % (main_message, message)
                    LoggerMessage.objects.create(
                        level=log_level, message=message, logger=log,)
#        а теперь отсылаем сообщение(если работаем с заявкой) и это действие не находится в исключениях
        if isinstance(obj, Requestion) and action_flag not in DISABLE_EMAIL_ACTIONS:
            profile = obj.profile
            if profile.user.email and profile.email_verified:
                context = scheme_and_domain()
                context.update({'requestion': log.content_object,
                    'user': log.user,
                    'change_type': log.get_action_flag_display(),
                    'changes_message': main_message})
                message = render_to_string("logger/emails/base.html", context)
                send_mail(subject=u"Изменение заявки %s" % extra['obj'],
                    message=message,
                    from_email=None, recipient_list=[obj.profile.user.email, ])

ANONYM_LOG = logging.DEBUG
ACCOUNT_LOG = logging.INFO
OPERATOR_LOG = logging.WARNING

LOG_LEVELS = (
    (ANONYM_LOG, u'Публичный'),
    (ACCOUNT_LOG, u'Авторизованные пользователи'),
    (OPERATOR_LOG, u'Оператор'),
)


class Logger(models.Model):
    u"""
    хранение логов выполненных действий
    """
    from sadiki.core.workflow import ACTION_CHOICES
    user = models.ForeignKey('auth.User', verbose_name=u"пользователь",
        null=True)
    reason = models.TextField(verbose_name=u"Основание",
        help_text=u"Внимание! Эта информация будет публично доступной, старайтесь не указывать персональные данные",
        null=True)
    datetime = models.DateTimeField(u"дата создания", auto_now_add=True)
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    added_pref_sadiks = models.ManyToManyField('core.Sadik',
        related_name='logger_added')
    removed_pref_sadiks = models.ManyToManyField('core.Sadik',
        related_name='logger_removed')
    vacancy = models.ForeignKey('core.Vacancies', null=True)
    age_groups = models.ManyToManyField('core.AgeGroup')
    profile = models.ForeignKey('core.Profile', null=True)
    action_flag = models.IntegerField(verbose_name=u'Произведенное действие',
                                      choices=ACTION_CHOICES)
    distribution_type = models.IntegerField(verbose_name=u'Тип распределения',
        choices=DISTRIBUTION_TYPE_CHOICES, null=True)

    objects = LoggerManager()


class LoggerMessageQuerySet(models.query.QuerySet):

    def filter_for_user(self, user):
        level_log = ANONYM_LOG
        if user.is_authenticated():
            if user.is_operator():
                level_log = OPERATOR_LOG
            elif user.is_requester():
                level_log = ACCOUNT_LOG
#                для пользователя показываем только его заявки
                user_requestions_ids = user.get_profile().requestion_set.all().values_list('id', flat=True)
                return self.filter(
                    Q(level=level_log, logger__object_id__in=user_requestions_ids,
                        logger__content_type=ContentType.objects.get_for_model(Requestion)) |
                    Q(level__lt=level_log))
        return self.filter(level__lte=level_log)


class LoggerMessage(models.Model):
    u"""
    хранение текстовых сообщений к логам для определенного уровня доступа
    """
    message = models.TextField(u"сообщение")
    level = models.PositiveIntegerField(u'уровень доступа',
        choices=LOG_LEVELS, default=logging.ERROR, blank=True, db_index=True)
    logger = models.ForeignKey(Logger)

    objects = query_set_factory(LoggerMessageQuerySet)

    class Meta:
        ordering = ['-level']

REPORT_FILLABILITY = 0
REPORT_TRANSITIONS = 1
REPORT_STATUSES = 2
REPORT_SADIKS_REQUESTS = 3

REPORT_DECISION_CHOICES = (
    (0, u"Первое распределение в году"),
    (1, u"Доукомплектование"),
    )

REPORTS_CHOICES = (
    (REPORT_FILLABILITY, u"Отчет о заполняемости ДОУ"),
    (REPORT_TRANSITIONS, u"Отчет по операциям в динамике"),
    (REPORT_STATUSES, u"Отчет по статусам обращений в разрезе муниципальных образований"),
    (REPORT_SADIKS_REQUESTS, u"Отчет по приему заявлений ДОУ"),
    )


class ReportQuerySet(models.query.QuerySet):

    def create_report(self, report_type, from_date, to_date, age_group=None,
        decision_type=None):
        from sadiki.logger.views import REPORTS_INFO
        kwargs = {"from_date": from_date, "to_date": to_date}
        if age_group:
            kwargs.update({"age_group": age_group})
        if decision_type:
            kwargs.update({"decision_type": decision_type})
        data = REPORTS_INFO["functions"][report_type](**kwargs)
        data_json = json.dumps(data, cls=DjangoJSONEncoder)
        return Report.objects.create(data=data_json, type=report_type,
            from_date=from_date, to_date=to_date, age_group=age_group, decision_type=decision_type)


class Report(models.Model):
    type = models.IntegerField(u"Тип отчета", choices=REPORTS_CHOICES)
    from_date = models.DateField(u"Дата начала отчетного периода")
    to_date = models.DateField(u"Дата окончания отчетного периода")
    data = models.TextField(verbose_name=u"Данные отчета")
    age_group = models.ForeignKey(u"core.AgeGroup", null=True)
    decision_type = models.IntegerField(u"Тип комплектования", null=True)
    objects = query_set_factory(ReportQuerySet)

    def get_data(self):
        return json.loads(self.data)

    def __unicode__(self):
        return u"%s с %s по %s" % (self.get_type_display(),
            self.from_date.strftime('%d-%m-%Y'),
            self.to_date.strftime('%d-%m-%Y'))
