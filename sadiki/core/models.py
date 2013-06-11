# -*- coding: utf-8 -*-
from Crypto.Cipher import ARC4
import random
from chunks.models import Chunk
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import GeoManager
from django.contrib.gis.db.models.fields import PolygonField, PointField
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models, transaction
from django.db.models.query_utils import Q
from django.db.models.signals import m2m_changed, post_save
from ordereddict import OrderedDict
from sadiki.conf_settings import MUNICIPALITY_OCATO
from sadiki.core.exceptions import TransitionNotRegistered
from sadiki.core.fields import BooleanNextYearField, YearChoiceField, \
    AreaChoiceField, SplitDayMonthField
from sadiki.core.utils import add_crc, calculate_luhn_digit, \
    get_current_distribution_year, get_qs_attr, get_user_by_email
from sadiki.core.validators import birth_date_validator, \
    registration_date_validator
from sadiki.settings import REQUESTER_USERNAME_PREFIX
from south.modelsinspector import add_introspection_rules
import datetime
import re


SEX_CHOICES = (
    (u'М', u'Мужской'),
    (u'Ж', u'Женский'),
)

STATUS_WAIT_REVIEW = 1  # Ожидает рассмотрения
STATUS_REJECTED = 2  # Заявление отклонено
STATUS_REQUESTER_NOT_CONFIRMED = 3  # Очередник - не подтвержден
STATUS_REQUESTER = 4  # Очередник
STATUS_DECISION = 6  # Принято решение о зачислении(выделено место в ДОУ)
STATUS_PASS_GRANTED = 9  # Выдана путевка (3Б,3В)
STATUS_TEMP_PASS_TRANSFER = 12  # Выдана путевка на временной основе (4А)
STATUS_DISTRIBUTED = 13  # Зачислен
STATUS_TEMP_DISTRIBUTED = 14  # Временно зачислен (4А)
STATUS_ABSENT = 15  # Отсутсвует
STATUS_NOT_APPEAR = 16  # Не явился
STATUS_REMOVE_REGISTRATION = 17  # Снят с учёта
STATUS_ARCHIVE = 18  # Архив
STATUS_ON_DISTRIBUTION = 50  # На комплектовании
STATUS_ON_TEMP_DISTRIBUTION = 51  # На временном комплектовании
STATUS_NOT_APPEAR_EXPIRE = 53  # Сроки на обжалование неявки истекли
STATUS_ABSENT_EXPIRE = 54  # Сроки на обжалование отсутствия истекли
STATUS_TEMP_ABSENT = 55  # Длительное отсутсвие по уважительной причине

STATUS_CHOICES = (
    (STATUS_WAIT_REVIEW, u'Ожидает рассмотрения'),
    (STATUS_REJECTED, u'Заявление отклонено'),
    (STATUS_REQUESTER_NOT_CONFIRMED, u'Очередник - не подтвержден'),
    (STATUS_REQUESTER, u'Очередник'),
    (STATUS_DECISION, u'Выделено место'),
    (STATUS_PASS_GRANTED, u'Выдана путевка'),

    (STATUS_TEMP_PASS_TRANSFER,
        u'Выдана путевка на временной основе'),
    (STATUS_DISTRIBUTED, u'Зачислен'),
    (STATUS_TEMP_DISTRIBUTED, u'Временно зачислен'),
    (STATUS_ABSENT, u'Отсутствует'),
    (STATUS_NOT_APPEAR, u'Не явился'),
    (STATUS_REMOVE_REGISTRATION, u'Снят с учёта'),
    (STATUS_ARCHIVE, u'Архивная'),
    (STATUS_ON_DISTRIBUTION, u'На комплектовании'),
    (STATUS_ON_TEMP_DISTRIBUTION, u'На временном комплектовании'),
    (STATUS_NOT_APPEAR_EXPIRE, u'Сроки на обжалование неявки истекли'),
    (STATUS_ABSENT_EXPIRE, u'Сроки на обжалование отсутствия истекли'),
    (STATUS_TEMP_ABSENT, u'Длительное отсутсвие по уважительной причине'),
)

REQUESTION_MUTABLE_STATUSES = (
    STATUS_WAIT_REVIEW,
    STATUS_REQUESTER_NOT_CONFIRMED,
    STATUS_REQUESTER)

REQUESTION_TYPE_OPERATOR = 0
REQUESTION_TYPE_IMPORTED = 1
REQUESTION_TYPE_CORRECTED = 2
REQUESTION_TYPE_NORMAL = 3

REQUESTION_TYPE_CHOICES = (
    (REQUESTION_TYPE_OPERATOR, u'Регистрация через оператора'),
    (REQUESTION_TYPE_IMPORTED, u'Импортированная заявка'),
    (REQUESTION_TYPE_CORRECTED, u'Заявка зарегистрирована до запуска системы и введена вручную'),
    (REQUESTION_TYPE_NORMAL, u'Cамостоятельная регистрация'),
)

def query_set_factory(query_set_class):
    u"""позволяет привязать методы как менеджера модели, так и для QuerySet"""
    class ChainedManager(models.Manager):

        def get_query_set(self):
            return query_set_class(self.model)

        def __getattr__(self, attr, *args):
            try:
                return getattr(self.__class__, attr, *args)
            except AttributeError:
                return getattr(self.get_query_set(), attr, *args)
    return ChainedManager()

PROFILE_IDENTITY = 0
REQUESTION_IDENTITY = 1
BENEFIT_DOCUMENT = 2

DOCUMENT_TEMPLATE_TYPES = (
    (PROFILE_IDENTITY, u'идентифицирует родителя'),
    (REQUESTION_IDENTITY, u'идентифицирует ребенка'),
    (BENEFIT_DOCUMENT, u'документы к льготам'),
    )

class EvidienceDocumentTemplate(models.Model):

    class Meta:
        verbose_name = u'Тип документа'
        verbose_name_plural = u'Типы документов'

    name = models.CharField(verbose_name=u'название', max_length=255)
    format_tips = models.CharField(verbose_name=u'подсказка к формату',
        max_length=255, blank=True)
    destination = models.IntegerField(
        verbose_name=u'назначение документа',
        choices=DOCUMENT_TEMPLATE_TYPES)
    regex = models.TextField(verbose_name=u'Регулярное выражение')

    def __unicode__(self):
        return self.name

class EvidienceDocumentQueryset(models.query.QuerySet):
    def confirmed(self):
        return self.filter(confirmed=True)

    def not_confirmed(self):
        return self.filter(confirmed=False)

    def documents_for_object(self, obj):
        return self.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id)

    def requestion_identity_documents(self):
        return self.filter(template__destination=REQUESTION_IDENTITY)


class EvidienceDocument(models.Model):

    class Meta:
        verbose_name = u'Документ'
        verbose_name_plural = u'Документы'

    template = models.ForeignKey(EvidienceDocumentTemplate,
        verbose_name=u'шаблон документа')
    document_number = models.CharField(u'Номер документа',
            max_length=255)
    confirmed = models.NullBooleanField(verbose_name=u'Подтвержден', default=None)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    fake = models.BooleanField(verbose_name=u'Был сгенерирован при импорте',
                               default=False)

    objects = query_set_factory(EvidienceDocumentQueryset)

    def clean(self):
        if self.pk:
            if not re.match(self.template.regex, self.document_number):
                raise ValidationError(u'Номер не соответвует формату %s' % self.template.format_tips)

    def make_other_appocryphal(self):
#        документы для льгот могут быть с совпадающими номерами
        if self.template.destination != BENEFIT_DOCUMENT:
            other_documents = EvidienceDocument.objects.filter(
                document_number=self.document_number,
                template=self.template)
            other_documents.update(confirmed=False)
            return other_documents
        return None

    def __unicode__(self):
        return self.document_number


class BenefitCategoryQueryset(models.query.QuerySet):

    def exclude_system_categories(self):
        return self.exclude(priority__gte=settings.BENEFIT_SYSTEM_MIN)

    def category_without_benefits(self):
        u"""Возврщаем категорию льгот с наименьшим приоритетом(подразумевается, что это категория без льгот)"""
        return self.all().order_by('priority')[0]

class BenefitCategory(models.Model):
    u"""Типы льгот"""

    class Meta:
        verbose_name = u"Категория льгот"
        verbose_name_plural = u"Категории льгот"

    name = models.CharField(verbose_name=u"Название", max_length=100)
    description = models.CharField(verbose_name=u"Описание", null=True,
        max_length=255)
    priority = models.IntegerField(verbose_name=u"Приоритетность льготы",
        help_text=u"Чем больше число, тем выше приоритет",
        validators=[MaxValueValidator(settings.BENEFIT_SYSTEM_MIN - 1)])
    immediately_distribution_active = models.BooleanField(
        verbose_name=u"Учавствует в немедленном зачислении", default=False)

    objects = query_set_factory(BenefitCategoryQueryset)

    def __unicode__(self):
        return self.name


class Benefit(models.Model):
    u"""Льготы"""

    class Meta:
        verbose_name = u'Льгота'
        verbose_name_plural = u'Льготы'

    category = models.ForeignKey("BenefitCategory", verbose_name=u'тип льгот')
    description = models.CharField(verbose_name=u'описание', max_length=255)
    name = models.CharField(verbose_name=u'название', max_length=255)
    evidience_documents = models.ManyToManyField(EvidienceDocumentTemplate,
        verbose_name=u"Необходимые документы")
    sadik_related = models.ManyToManyField("Sadik",
        verbose_name=u"ДОУ в которых есть группы", blank=True, null=True,)

    def __unicode__(self):
        return self.name


class Address(models.Model):

    class Meta:
        verbose_name = u'Адрес'
        verbose_name_plural = u'Адреса'

    town = models.CharField(verbose_name=u"Населенный пункт",
                            max_length=255, blank=True, null=True)
    street = models.CharField(verbose_name=u'текст адреса',
        max_length=255, blank=False, null=True)
    postindex = models.IntegerField(verbose_name=u'почтовый индекс',
        validators=[MaxValueValidator(999999)], blank=True, null=True)
    ocato = models.CharField(verbose_name=u'ОКАТО', max_length=11,
        blank=True, null=True)
    block_number = models.CharField(verbose_name=u'№ квартала',
        max_length=255, blank=True, null=True)
    building_number = models.CharField(verbose_name=u'№ здания',
        max_length=255, blank=True, null=True)
    extra_info = models.TextField(
        verbose_name=u'дополнительная информация', blank=True, null=True)
    kladr = models.CharField(verbose_name=u'КЛАДР', max_length=255,
        blank=True, null=True)
    coords = PointField(verbose_name=u'Координаты точки', blank=True, null=True)

    objects = GeoManager()

    @property
    def text(self):
        address_elements = []
        if self.town:
            town = "%s," % self.town
            address_elements.append(town)
        if self.building_number and self.street:
            street = "%s," % self.street
        else:
            street = self.street
        address_elements.extend([self.block_number, street, self.building_number])
        return u" ".join([el for el in address_elements if el])

    def __unicode__(self):
        return self.text


class SadikQueryset(models.query.QuerySet):

    def filter_for_profile(self, profile):
        if profile.sadiks.exists():
            return self.filter(id__in=profile.sadiks.all().values_list('id', flat=True))
        else:
            if profile.area:
                return self.filter(area=profile.area)
        return self
    
    def add_related_groups(self, only_active=False):
#        а здесь начинается магия... нам нужно вытянуть M2One sadik_groups
#        а как же prefetch_related? пока что используется dj 1.3, так что при случае можно будет заменить
        sadiks_dict = OrderedDict([(sadik.id, sadik) for sadik in self])
#        и сразу захватим с собой имена возрастных групп
        sadik_groups = SadikGroup.objects.active().filter(sadik__in=self
            ).select_related("age_group__name")
        if only_active:
            sadik_groups = sadik_groups.active()
        relation_dict = {}
        for sadik_group in sadik_groups:
            relation_dict.setdefault(sadik_group.sadik_id, []).append(sadik_group)
        for id, related_groups in relation_dict.items():
            sadiks_dict[id].related_groups = related_groups

class Sadik(models.Model):
    u"""Класс садика"""

    class Meta:
        verbose_name = u'ДОУ'
        verbose_name_plural = u'ДОУ'
        ordering = ['number']

    area = models.ForeignKey("Area", verbose_name=u"Территориальная область")
    name = models.CharField(u'полное название', max_length=255)
    short_name = models.CharField(u'короткое название', max_length=255)
    number = models.IntegerField(u'номер', null=True)
    identifier = models.CharField(u'идентификатор', null=True, max_length=25)
    address = models.ForeignKey("Address", verbose_name=u"Адрес")
    email = models.CharField(u'электронная почта',
        max_length=255, blank=True)
    site = models.CharField(u'сайт', max_length=255, blank=True,
        null=True)
    head_name = models.CharField(u'ФИО директора (заведующей)', max_length=255)
    phone = models.CharField(u'телефон', max_length=255,
        blank=True, null=True)
    cast = models.CharField(u'тип(категория) ДОУ', max_length=255, blank=True)
    # TODO: Вынести фотографии в отдельный модуль, например, администрирования
#    photos = models.ManyToManyField("Photo", blank=True, null=True)
    tech_level = models.TextField(u'техническая оснащенность',
        blank=True, null=True)
    training_program = models.TextField(
        u'учебные программы дополнительного образования',
        blank=True, null=True)
    route_info = models.ImageField(u'схема проезда',
        upload_to=u'upload/sadiki/routeinfo/', blank=True, null=True)
    # Дополнительные поля
    extended_info = models.TextField(
        u'дополнительная информация',
        blank=True, null=True)
    active_registration = models.BooleanField(
        verbose_name=u'может быть указан как приоритетный', default=True)
    active_distribution = models.BooleanField(
        verbose_name=u'принимает участие в распределении', default=True)
    age_groups = models.ManyToManyField("AgeGroup",
        verbose_name=u"Возрастные группы")
    objects = query_set_factory(SadikQueryset)

    def get_number(self):
        result = re.match(ur'^\D*(\d+)\D*$', self.short_name)
        if result:
            return result.group(1)
        else:
            return None

    def save(self, *args, **kwargs):
        # обновляем номер ДОУ
        self.number = self.get_number()
        return super(Sadik, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.short_name or self.name

SADIK_GROUP_TYPE_NORMAL = 0
SADIK_GROUP_TYPE_CORRECTION = 1
SADIK_GROUP_TYPE_CHOICES = (
    (SADIK_GROUP_TYPE_NORMAL, u'Обычная'),
    (SADIK_GROUP_TYPE_CORRECTION, u'Коррекционная'),
    )

class AgeGroup(models.Model):
    u"""
    Возрастная группа для детсада. Эти группы глобальны для всей системы
    """
    class Meta:
        verbose_name = u'Возрастная группа для системы'
        verbose_name_plural = u'Возрастные группы для системы'
        ordering = ['from_age']

    name = models.CharField(u'название', max_length=255)
    short_name = models.CharField(u'короткое название', max_length=100, null=True)
    from_age = models.IntegerField(u'Минимальный возраст',
        help_text=u'полных месяцев на дату исполнения минимального возраста')
    # TODO: создать поле для ежегодной даты
    from_date = SplitDayMonthField(u'Дата исполнения минимального возраста',
        max_length=10, help_text=u"""укажите дату(число и месяц) на 
        которую будет рассчитываться минимальный возраст""")
    to_age = models.IntegerField(u'Максимальный возраст',
            help_text=u'полных месяцев на дату исполнения максимального возраста')
    to_date = SplitDayMonthField(verbose_name=u'Дата исполнения максимального возраста',
        max_length=10, help_text=u"""укажите дату(число и месяц) на 
        которую будет рассчитываться максимальный возраст""")
    next_age_group = models.ForeignKey("core.AgeGroup",
        verbose_name=u'Следующая возрастная группа', blank=True, null=True)

    def max_birth_date(self, current_distribution_year=None):
        if not current_distribution_year:
            current_distribution_year = get_current_distribution_year()
        day, month = [int(number) for number in self.from_date.split('.')]
        return current_distribution_year.replace(
            day=day, month=month) + relativedelta(months= -self.from_age)

    def min_birth_date(self, current_distribution_year=None):
        if not current_distribution_year:
            current_distribution_year = get_current_distribution_year()
        day, month = [int(number) for number in self.to_date.split('.')]
        return current_distribution_year.replace(
            day=day, month=month) + relativedelta(months= -self.to_age)

    def __unicode__(self):
        return self.name

class SadikGroupQueryset(models.query.QuerySet):
    def active(self):
        u"""исключаются все группы, принадлежащие к завершившися зачислениям"""
        return self.filter(active=True)

    def appropriate_for_birth_date(self, birth_date):
        u"""только те, которые подходят для заданной даты рождения"""
        return self.filter(min_birth_date__lt=birth_date,
            max_birth_date__gte=birth_date)

class SadikGroup(models.Model):
    class Meta:
        verbose_name = u'Расчётная группа детского сада'
        verbose_name_plural = u'Расчётные группы детского сада'
        ordering = ['-min_birth_date']

    age_group = models.ForeignKey('AgeGroup', blank=True, null=True)
    other_name = models.CharField(u'Альтернативное имя', max_length=100,
        blank=True, null=True)
    cast = models.IntegerField(u'тип', choices=SADIK_GROUP_TYPE_CHOICES,
        default=SADIK_GROUP_TYPE_NORMAL)
    sadik = models.ForeignKey(Sadik, null=False, blank=False,
        related_name='groups')
    capacity = models.PositiveIntegerField(u'номинальная вместимость', default=0)
    free_places = models.PositiveIntegerField(u'кол-во свободных мест', default=0)
    distributions = models.ManyToManyField('Distribution',
        through='Vacancies')
    # Возрастные параметры
    min_birth_date = models.DateField(verbose_name=u'Наименьший возраст')
    max_birth_date = models.DateField(verbose_name=u'Наибольший возраст')
    year = models.DateField(verbose_name=u'Год распределения')
    active = models.BooleanField(verbose_name=u'Активна', default=True,
        help_text=u'Если группа активна, то в неё можно зачислять детей')

    objects = query_set_factory(SadikGroupQueryset)

    def set_default_age(self, age_group):
#        вычисляем возрастные ограничения
        self.min_birth_date = age_group.min_birth_date
        self.max_birth_date = age_group.max_birth_date
        
    def appropriate_for_birth_date(self, birth_date):
        return self.min_birth_date<birth_date and self.max_birth_date>birth_date

    def __unicode__(self):
        if self.pk:
            name = self.other_name or self.age_group.name
            return u"%s за %d год" % (name, self.year.year)
        else:
            return u"новая группа"

def update_vacancies(sender, **kwargs):
    sadik_group = kwargs['instance']
    if not Distribution.objects.active():
        vacancies = Vacancies.objects.filter(distribution__isnull=True,
            status__isnull=True, sadik_group=sadik_group)
        free_vacancies_number = vacancies.count()
        places_sub = free_vacancies_number - sadik_group.free_places
#            если кол-во путевок больше свободных мест, то нужно удалить лишние
        if places_sub > 0:
            vacancies_to_delete = vacancies[0:places_sub]
            Vacancies.objects.filter(id__in=vacancies_to_delete).delete()
#            если кол-во путевок меньше свободных мест, досоздаем
        elif places_sub < 0:
            for i in range(abs(places_sub)):
                Vacancies.objects.create(sadik_group=sadik_group)

post_save.connect(update_vacancies, sender=SadikGroup)


VACANCY_STATUS_PROVIDED = 0
VACANCY_STATUS_MANUALLY_DISTRIBUTING = 4
VACANCY_STATUS_MANUALLY_CHANGED = 5
VACANCY_STATUS_DISTRIBUTED = 1
VACANCY_STATUS_TEMP_ABSENT = 2
VACANCY_STATUS_TEMP_DISTRIBUTED = 3

VACANCY_STATUS_CHOICES = (
    (None, u"Место свободно"),
    (VACANCY_STATUS_PROVIDED, u"Выделено место"),
    (VACANCY_STATUS_MANUALLY_DISTRIBUTING, u"На ручном распределении"),
    (VACANCY_STATUS_MANUALLY_CHANGED, u"Перераспределена вручную"),
    (VACANCY_STATUS_DISTRIBUTED, u"Зачислена"),
    (VACANCY_STATUS_TEMP_ABSENT, u"Отсутствует по уважительной причине"),
    (VACANCY_STATUS_TEMP_DISTRIBUTED, u"Временная путевка"),
    )


class Vacancies(models.Model):
    sadik_group = models.ForeignKey('SadikGroup')
    distribution = models.ForeignKey('Distribution', blank=True, null=True)
    status = models.IntegerField(u"статус", choices=VACANCY_STATUS_CHOICES,
        null=True)

    def to_manual_distribution(self):
        assert self.status in (VACANCY_STATUS_PROVIDED, VACANCY_STATUS_MANUALLY_CHANGED)
        self.status = VACANCY_STATUS_MANUALLY_DISTRIBUTING
        self.save()

    def get_distributed_requestion(self):
        try:
            return self.requestion_set.get(status=STATUS_DISTRIBUTED)
        except Requestion.DoesNotExist:
            return None

    def get_absent_requestion(self):
        try:
            return self.requestion_set.get(status=STATUS_TEMP_ABSENT)
        except Requestion.DoesNotExist:
            return None

    @property
    def changed_manually(self):
        return self.status is VACANCY_STATUS_MANUALLY_CHANGED

    @property
    def distance(self):
        u"""Расстояние по прямой от ребенка до садика"""
        sadik_coords = self.sadik_group.sadik.address.coords
        child_coords = self.requestion_set.all()[0].address.coords
        if sadik_coords and child_coords:
            return sadik_coords.distance(child_coords)

    def __unicode__(self):
        if self.status is not None:
            return u'Путевка №%s (%s)' % (self.id, self.get_status_display())
        else:
            return u'Свободная путевка №%s' % self.id

DISTRIBUTION_STATUS_INITIAL = 0
DISTRIBUTION_STATUS_START = 1
DISTRIBUTION_STATUS_END = 2
DISTRIBUTION_STATUS_AUTO = 3
DISTRIBUTION_STATUS_ENDING = 4

DISTRIBUTION_STATUS_CHOICES = (
    (DISTRIBUTION_STATUS_INITIAL, u'Распределение начато'),
    (DISTRIBUTION_STATUS_AUTO, u'Автоматическое комплектование'),
    (DISTRIBUTION_STATUS_START, u'Комплектация заявок'),
    (DISTRIBUTION_STATUS_ENDING, u'Процесс завершения распределения'),
    (DISTRIBUTION_STATUS_END, u'Распределение завершено'),
    )


class DistributionQuerySet(models.query.QuerySet):
    def active(self):
        try:
            distribution = Distribution.objects.get(
                status__in=(DISTRIBUTION_STATUS_INITIAL,
                    DISTRIBUTION_STATUS_START, DISTRIBUTION_STATUS_AUTO))
        except Distribution.DoesNotExist:
            distribution = None
        return distribution


class Distribution(models.Model):
    class Meta:
        verbose_name = u'Распределение'
        verbose_name_plural = u'Распределения'

    init_datetime = models.DateTimeField(
        verbose_name=u"Дата и время начала выделения мест", auto_now_add=True)
    start_datetime = models.DateTimeField(
        verbose_name=u'Дата и время начала распределения', blank=True,
        null=True)
    end_datetime = models.DateTimeField(verbose_name=u'Дата и время окончания',
        blank=True, null=True)
    status = models.IntegerField(verbose_name=u'Текущий статус',
        choices=DISTRIBUTION_STATUS_CHOICES,
        default=DISTRIBUTION_STATUS_INITIAL)
    year = models.DateField(verbose_name=u'Год распределения')

    objects = query_set_factory(DistributionQuerySet)

    def is_initial(self):
        return self.status == DISTRIBUTION_STATUS_INITIAL

    def is_started(self):
        return self.status == DISTRIBUTION_STATUS_START

    def is_finished(self):
        return self.status == DISTRIBUTION_STATUS_END

    def distributed_requestions(self):
        Requestion.objects.queue().confirmed().filter(
            status=STATUS_DECISION, distribute_in_group_info__distribution=self)


AGENT_TYPE_MOTHER = 0
AGENT_TYPE_FATHER = 1
AGENT_TYPE_TUTOR = 2
AGENT_TYPE_OTHER = 3

AGENT_TYPE_CHOICES = (
    (AGENT_TYPE_MOTHER, u"мать"),
    (AGENT_TYPE_FATHER, u"отец"),
    (AGENT_TYPE_TUTOR, u"опекун"),
    (AGENT_TYPE_OTHER, u"иное"),
    )

class Profile(models.Model):
    u"""Класс профиля пользователя"""
    # Profile data
    class Meta:
        verbose_name = u'Профиль родителя'
        verbose_name_plural = u'Профили родителей'

    user = models.OneToOneField('auth.User', verbose_name=u'Пользователь',
        unique=True)
    area = models.ForeignKey('Area',
        verbose_name=u'Территориальная область к которой относится', null=True)
    first_name = models.CharField(u'Имя', max_length=255, null=True)
    nickname = models.CharField(u'Псевдоним', max_length=255, null=True, help_text=u"Как к Вам обращаться?")
    email_verified = models.BooleanField(u'E-mail достоверный',
        default=False)
    phone_number = models.CharField(u'Телефон для связи', max_length=255,
        blank=False, null=True,
        help_text=u"Номер телефона для связи")
    mobile_number = models.CharField(u'Дополнительный телефон',
        max_length=255, blank=True, null=True,
        help_text=u"Дополнительный номер телефона для связи")
    skype = models.CharField(u'Skype',
        max_length=255, blank=True, null=True,
        help_text=u"Учетная запись в сервисе Skype")
    sadiks = models.ManyToManyField('Sadik', null=True)

    def get_identity_documents(self):
        return EvidienceDocument.objects.documents_for_object(self)

    def sadik_available(self, sadik):
        u"""проверка есть ли у пользователя права на ДОУ"""
        return (self.area == sadik.area if self.area else True
            and self.sadiks.filter(id=sadik.id).exists()
                if self.sadiks.exists() else True)

    def social_auth_clean_data(self):
        self.phone_number = None
        self.first_name = None
        self.skype = None

    def update_vkontakte_data(self, data):
        self.first_name = data.get('first_name')
        self.phone_number = data.get('home_phone')
        self.skype = data.get('skype')



    def __unicode__(self):
        return self.user.username

NOT_CONFIRMED_STATUSES = (
    STATUS_WAIT_REVIEW,
    STATUS_REJECTED,
    STATUS_REQUESTER_NOT_CONFIRMED,
    STATUS_REMOVE_REGISTRATION,
    STATUS_ARCHIVE,
    )

DISTRIBUTION_PROCESS_STATUSES = (
    STATUS_DECISION,
    STATUS_PASS_GRANTED,
    STATUS_ABSENT,
    STATUS_ABSENT_EXPIRE,
    STATUS_NOT_APPEAR,
    STATUS_NOT_APPEAR_EXPIRE,
    )

DEFAULT_DISTRIBUTION_TYPE = 0
PERMANENT_DISTRIBUTION_TYPE = 1

DISTRIBUTION_TYPE_CHOICES = (
    (DEFAULT_DISTRIBUTION_TYPE, u'Обычное зачисление'),
    (PERMANENT_DISTRIBUTION_TYPE, u'Зачисление на постоянной основе'),
    )

class RequestionQuerySet(models.query.QuerySet):

    def queue(self):
        u"""возвращает заявки, отображаемые в очереди"""
        return self.filter(
            status__in=(STATUS_REQUESTER_NOT_CONFIRMED, STATUS_REQUESTER,
                        STATUS_DECISION, STATUS_ON_DISTRIBUTION,
                        STATUS_DISTRIBUTED,
                        STATUS_TEMP_DISTRIBUTED,
                        STATUS_ON_TEMP_DISTRIBUTION,
                        STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE,
                        )).order_by(
                '-benefit_category__priority', 'registration_datetime', 'id')

    def not_distributed(self):
        u"""Все заявки, которым можно выделить места"""
        return self.filter(
            status__in=(STATUS_REQUESTER, STATUS_TEMP_DISTRIBUTED,)).order_by(
                '-benefit_category__priority', 'registration_datetime', 'id')

    def decision_requestions(self):
        return self.filter(
            status=STATUS_DECISION).order_by(
                '-benefit_category__priority', 'registration_datetime', 'id')

    def provided_places(self):
        u"""
        Заявки которые занимают место в ДОУ(выделено место, зачислена, не явился(но еще не снят с учета))
        """
        return self.filter(status__in=(STATUS_DECISION, STATUS_DISTRIBUTED,
                                       STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE))

    def not_confirmed(self):
        u"""заявки для которых не установлено документальное подтверждение"""
        return self.filter(status__in=NOT_CONFIRMED_STATUSES)

    def confirmed(self):
        u"""
        заявки для которых установлено документальное подтверждение
        """
        return self.exclude(status__in=NOT_CONFIRMED_STATUSES)

    def _sorting_to_kwds(self, instance, sort_param):
        u"""Берет у объекта ``instance`` параметр ``sort_param``
         и возвращает словарь для построения фильтра объектов,
         стоящих в сортировке перед ``instance`` включительно.
         см. метод ``requestions_before``.
        """
        if sort_param.startswith('-'):
            return {'%s__gt' % sort_param[1:]: get_qs_attr(instance, sort_param[1:])}
        else:
            return {'%s__lt' % sort_param: get_qs_attr(instance, sort_param)}

    def requestions_before(self, instance):
        u"""
        Возвращает список заявок, учитывая сортировку запроса, находящихся перед
        заявкой ``instance`` в выдаче с сортировкой **включая** саму заявку.
        """
        if self.ordered:
            order_fields = self.query.order_by

            q_object = None
            for n, current_sort_param in enumerate(order_fields):
                kwds = self._sorting_to_kwds(instance, current_sort_param)
                for sort_param in order_fields[0:n]:
                    sort_param = sort_param.strip('-')
                    kwds.update({sort_param: get_qs_attr(instance, sort_param)})
                if q_object:
                    q_object = q_object | Q(**kwds)
                else:
                    q_object = Q(**kwds)

            return self.filter(q_object)
        else:
            return self

    def benefits(self):
        return self.filter(benefit_category__priority__gt=0)

    def filter_for_age(self, min_birth_date, max_birth_date):
        return self.filter(Q(birth_date__gt=min_birth_date), Q(birth_date__lte=max_birth_date))

    def add_distributed_sadiks(self):
        return self.extra(select={
            'distribute_in_sadik_id': '''SELECT core_sadikgroup.sadik_id FROM core_sadikgroup
                WHERE core_sadikgroup.id=(
                SELECT core_vacancies.sadik_group_id FROM core_vacancies
                WHERE core_vacancies.id = core_requestion.distributed_in_vacancy_id)''',
            'sadik_name': '''SELECT core_sadik.short_name
                FROM core_sadikgroup INNER JOIN core_sadik ON core_sadikgroup.sadik_id = core_sadik.id
                WHERE core_sadikgroup.id = (
                SELECT core_vacancies.sadik_group_id FROM core_vacancies
                WHERE core_vacancies.id = core_requestion.distributed_in_vacancy_id)'''
            })

    def enrollment_in_progress(self):
        return self.filter(status__in=(STATUS_DECISION, STATUS_ABSENT, STATUS_ABSENT_EXPIRE, STATUS_NOT_APPEAR,
            STATUS_NOT_APPEAR_EXPIRE))

    def add_related_documents(self):
#        а здесь начинается магия... нам нужно вытянуть M2One sadik_groups
#        а как же prefetch_related? пока что используется dj 1.3, так что при случае можно будет заменить
        requestions_dict = OrderedDict([(requestion.id, requestion) for requestion in self])
#        и сразу захватим с собой имена возрастных групп
        documents = EvidienceDocument.objects.filter(object_id__in=self.values_list('id', flat=True
                ), content_type=ContentType.objects.get_for_model(Requestion)).requestion_identity_documents(
            ).select_related('template__name')
        relation_dict = {}
        for document in documents:
            relation_dict.setdefault(document.object_id, []).append(document)
        for id, related_documents in relation_dict.items():
            requestions_dict[id].related_documents = related_documents


class Requestion(models.Model):
    u"""Класс для заявки на зачисление в ДОУ"""

    class Meta:
        verbose_name = u'Заявка в очереди'
        verbose_name_plural = u'Заявки в очереди'

    areas = AreaChoiceField('Area',
        verbose_name=u'Предпочитаемые территориальные области',
        help_text=u"""Территориальная область в которой вы хотели бы посещать ДОУ.""")

    # Child data
    if settings.DESIRED_DATE == settings.DESIRED_DATE_NO:
        admission_date = models.DateField(u'Желаемая дата поступления',
            default=None, editable=False,
            help_text=u"Дата, начиная с которой заявка может быть зачислена")
    elif settings.DESIRED_DATE == settings.DESIRED_DATE_NEXT_YEAR:
        admission_date = BooleanNextYearField(u'Немедленное зачисление',
            blank=True, null=True,
            help_text=u"Если не выбрано, то заявка может быть распределена \
                только во время ближайшего массового комплектования")
    elif settings.DESIRED_DATE == settings.DESIRED_DATE_SPEC_YEAR:
        admission_date = YearChoiceField(u'Желаемый год поступления',
            blank=True, null=True,
            help_text=u"Год, начиная с которого заявка может быть зачислена")
    elif settings.DESIRED_DATE == settings.DESIRED_DATE_ANY:
        admission_date = models.DateField(u'Желаемая дата поступления',
            blank=True, null=True,
            help_text=u"Дата, начиная с которой заявка может быть зачислена")
    else:
        raise NotImplementedError('settings.DESIRED_DATE value %s not supported' % settings.DESIRED_DATE)
#    admission_date_type = models.IntegerField(u'тип желаемой даты поступления',
#        choices=ADMISSION_DATE_TYPE_CHOICES)
    requestion_number = models.CharField(verbose_name=u'Номер заявки',
        max_length=23, blank=True, null=True)
    distribution_type = models.IntegerField(
        verbose_name=u'тип распределения', choices=DISTRIBUTION_TYPE_CHOICES,
        default=DEFAULT_DISTRIBUTION_TYPE)
#    используется для хранения путевки, которая выдана ребенку
#    (например при переводе или постоянном зачислении), чтобы можно было вернуть
    previous_distributed_in_vacancy = models.ForeignKey(
        'Vacancies', blank=True, null=True,
        related_name=u"previous_requestions")
    distributed_in_vacancy = models.ForeignKey(
        'Vacancies', blank=True, null=True)

#    Child info
    birth_date = models.DateField(u'Дата рождения ребенка', validators=[birth_date_validator])
    name = models.CharField(u'имя ребёнка', max_length=255, null=True,
                            help_text=u"В поле достаточно ввести только имя ребенка. Фамилию и отчество вводить не нужно!")
    sex = models.CharField(max_length=1, verbose_name=u'Пол ребёнка',
        choices=SEX_CHOICES, null=True)
    cast = models.IntegerField(verbose_name=u'Тип заявки',
        choices=REQUESTION_TYPE_CHOICES, default=REQUESTION_TYPE_NORMAL)
    status = models.IntegerField(verbose_name=u'Статус', choices=STATUS_CHOICES,
        null=True, default=STATUS_REQUESTER_NOT_CONFIRMED)
    registration_datetime = models.DateTimeField(
        verbose_name=u'Дата и время подачи заявки',
        default=datetime.datetime.now, validators=[registration_date_validator])
    number_in_old_list = models.CharField(verbose_name=u'Номер в бумажном списке',
        max_length=15, blank=True, null=True)
    benefits = models.ManyToManyField(Benefit, blank=True, verbose_name=u'Льготы')
    benefit_category = models.ForeignKey("BenefitCategory",
        verbose_name=u"Категория льгот", null=True)
    pref_sadiks = models.ManyToManyField('Sadik')
    profile = models.ForeignKey('Profile', verbose_name=u'Профиль заявителя')
    location = PointField(verbose_name=u'Местоположение', blank=True, null=True,
                          help_text=u"Относительно этого местоположения будут определятся ближайшие ДОУ")
    location_properties = models.CharField(verbose_name=u'Параметры местоположения',
                                           max_length=250, blank=True, null=True)

    # Поля, назначаемые системой
    status_change_datetime = models.DateTimeField(
        verbose_name=u'дата и время последнего изменения статуса', blank=True, null=True)
    decision_datetime = models.DateTimeField(
        verbose_name=u'дата и время выделения места', blank=True, null=True)
    distribution_datetime = models.DateTimeField(
        verbose_name = u"дата и время окончательного зачисления", blank=True, null=True)

    # Flags
    distribute_in_any_sadik = models.BooleanField(
        verbose_name=u'Пользователь согласен на зачисление в ДОУ, отличные от приоритетных, в выбранных территориальных областях',
        default=False, help_text=u"""Установите этот флаг, если готовы получить место в любом детском саду в выбранных
            территориальных областях, в случае, когда в приоритетных ДОУ не окажется места""")

    objects = query_set_factory(RequestionQuerySet)

    def get_requestion_number(self):
        id_with_crc = add_crc(self.id)
        id_with_crc_str = chr(id_with_crc & 0xFF) + chr(id_with_crc >> 8 & 0xFF) + chr(id_with_crc >> 16 & 0xFF)
        arc = ARC4.new(settings.SECRET_KEY[:3])
        unic_number_str = arc.encrypt(id_with_crc_str)
        unic_number = ord(unic_number_str[0]) | ord(unic_number_str[1]) << 8 | ord(unic_number_str[2]) << 16
        luhn_digit = calculate_luhn_digit(unic_number)
        return u"%s-Б-%s%d" % (MUNICIPALITY_OCATO,
            str(unic_number).zfill(8), luhn_digit)

    def evidience_documents(self):
        return EvidienceDocument.objects.filter(
                content_type=ContentType.objects.get_for_model(self.__class__),
                object_id=self.id)

    def get_other_ident_documents(self, confirmed=False):
#        !!!! Bug in empty queryset with values_list return non empty value https://code.djangoproject.com/ticket/17712
        try:
            document = self.evidience_documents().get(
                template__destination=REQUESTION_IDENTITY)
        except EvidienceDocument.DoesNotExist:
            return EvidienceDocument.objects.none()
        else:
            documents = EvidienceDocument.objects.filter(
                template=document.template,
                document_number=document.document_number).exclude(
                    object_id=self.id,
                    content_type=ContentType.objects.get_for_model(self)).exclude(
                        confirmed=False)
            if confirmed:
                documents = documents.confirmed()
            return documents

    def other_requestions_with_ident_document(self):
        documents = self.get_other_ident_documents()
        if documents.exists():
            requestions_ids = documents.values_list('object_id', flat=True)
            return Requestion.objects.filter(id__in=requestions_ids)
        else:
            return Requestion.objects.none()

    def set_ident_document_authentic(self):
        from sadiki.logger.models import Logger
        from sadiki.core.workflow import NOT_CONFIRMED_REMOVE_REGISTRATION
#        помечаем документ, идентифицирующий заявку, как достоверный
        try:
            document = self.evidience_documents().get(
                template__destination=REQUESTION_IDENTITY)
        except EvidienceDocument.DoesNotExist:
            return []
        else:
            document.confirmed = True
            document.save()
    #        остальные документы с таким номером недостоверны
            other_documents = self.get_other_ident_documents()
            other_requestions = []
            for document in other_documents:
                document.confirmed = False
                document.save()
                requestion = document.content_object
                other_requestions.append(requestion)
                requestion.status = STATUS_REMOVE_REGISTRATION
                requestion.save()
                Logger.objects.create_for_action(NOT_CONFIRMED_REMOVE_REGISTRATION,
                    context_dict={'other_requestion': self},
                    extra={'obj': requestion})
            return other_requestions

    def set_benefit_documents_authentic(self):
#        документы для льгот выставляем достоверными(другие док-ты с таким номером не трогаем)
        self.evidience_documents().filter(
            template__destination=BENEFIT_DOCUMENT).update(confirmed=True)

    def set_document_unauthentic(self):
        try:
            document = self.evidience_documents().get(
                template__destination=REQUESTION_IDENTITY)
        except EvidienceDocument.DoesNotExist:
            pass
        else:
            document.confirmed = False
            document.save()

    def document_confirmed(self):
        return self.status not in NOT_CONFIRMED_STATUSES

    def get_sadiks_groups(self):
        groups = SadikGroup.objects.appropriate_for_birth_date(self.birth_date
            ).filter(free_places__gt=0)
        if self.areas.count():
            groups.filter(sadik__area__id__in=self.areas.all().values_list('id', flat=True))
        else:
            return groups

    def get_sadik_groups(self, sadik):
        return SadikGroup.objects.appropriate_for_birth_date(
                    self.birth_date).filter(sadik=sadik)

    def age_groups(self, age_groups=None, current_distribution_year=None):
        if not age_groups:
            age_groups = AgeGroup.objects.all()
        return filter(lambda group: group.min_birth_date(current_distribution_year) < self.birth_date <= group.max_birth_date(current_distribution_year),
            age_groups)

    def days_for_appeal(self):
        u"""
        возвращается кол-во дней, оставшихся до окончания обжалования
        округление производится в больщую сторону(если осталось меньше дня,
        возвращаетсяs 1 день)
        """
        status_change_delta = datetime.datetime.now() - self.status_change_datetime
        delta_for_appeal = datetime.timedelta(days=settings.APPEAL_DAYS) - status_change_delta
        if delta_for_appeal.days >= -1:
            return delta_for_appeal.days + 1
        else:
            return 0

    @property
    def editable(self):
        return self.status in REQUESTION_MUTABLE_STATUSES

    def available_temp_vacancies(self):
        return Vacancies.objects.filter(
            status=VACANCY_STATUS_TEMP_ABSENT, sadik_group__active=True,
            sadik_group__max_birth_date__gte=self.birth_date,
            sadik_group__min_birth_date__lt=self.birth_date)

    def _distribute_in_sadik(self, sadik):
        u"""Функция помощник для зачисления в садик
        Статус заявки не меняется
        """
        self.status = STATUS_DECISION
        self.previous_distributed_in_vacancy = self.distributed_in_vacancy
        sadik_groups = self.get_sadik_groups(sadik=sadik)

        assert (Vacancies.objects.filter(sadik_group__in=sadik_groups,
            status__isnull=True).exists()), u'В садике должны быть путевки'

        vacancy = Vacancies.objects.filter(sadik_group__in=sadik_groups,
            status__isnull=True)[0]
        self.distributed_in_vacancy = vacancy
        vacancy.status = VACANCY_STATUS_PROVIDED
        sadik_group = vacancy.sadik_group
        sadik_group.free_places -= 1
        sadik_group.save()
        vacancy.save()
        self.save()
        return vacancy

    def distribute_in_sadik_from_requester(self, sadik):
        u"""
        распределение в указанный ДОУ, возвращается путевка.
        """
        self.status = STATUS_DECISION
        return self._distribute_in_sadik(sadik)

    def distribute_in_sadik_from_tempdistr(self, sadik):
        u"""Зачисление на постоянной основе из временно зачисленных"""
        self.distribution_type = PERMANENT_DISTRIBUTION_TYPE
        return self._distribute_in_sadik(sadik)

    def permanent_distribution(self):
        return self.distribution_type == PERMANENT_DISTRIBUTION_TYPE

    def get_vacancy_distributed(self):
        u"""
        возвращает путевку в которую заявка уже распределена
        """
        if self.status == STATUS_DISTRIBUTED:
            return self.distributed_in_vacancy
        else:
            return None

    def get_vacancy_temp_distributed(self):
        u"""
        возвращает путевку в которую временно распределена заявка
        """
        if self.status in (STATUS_TEMP_DISTRIBUTED,
                STATUS_ON_TEMP_DISTRIBUTION):
            return self.distributed_in_vacancy
        elif (self.status in DISTRIBUTION_PROCESS_STATUSES and
                self.distribution_type == PERMANENT_DISTRIBUTION_TYPE):
            return self.previous_distributed_in_vacancy
        else:
            return None

    def get_vacancy_decision(self):
        u"""
        Возвращается путевка в которую производится распределение заявки
        """
        if self.status in DISTRIBUTION_PROCESS_STATUSES:
            return self.distributed_in_vacancy

    def save(self, *args, **kwargs):
        u"""
        Осуществляется проверка возможности изменения статуса.
        Сохраняется дата последнего изменения статуса, дата выделения места и дата зачисления.
        Если сохраняется в первый раз(добавление заявки), то определяем статус
        и генерируем номер заявки
        """
#        проверяем изменился ли статус
        if self.id:
            status = Requestion.objects.get(id=self.id).status
        else:
            status = None
#            проверяем, что задана категория льгот, если нет, то задаем с наименьшим
#            приоритетом
            if not self.benefit_category:
                self.benefit_category = BenefitCategory.objects.all(
                    ).order_by('priority')[0]
#            если возможность зачисления не в приоритетные ДОУ задана вариантом
#            реализации, то при создании заявки задаем параметр
            if settings.DESIRED_SADIKS == settings.DESIRED_SADIKS_ONLY:
                self.distribute_in_any_sadik = False
            elif settings.DESIRED_SADIKS == settings.DESIRED_SADIKS_ANY:
                self.distribute_in_any_sadik = True
        if status != self.status:
            # Проверка на допустимость изменения статуса
            from sadiki.core.workflow import workflow
            if self.status not in workflow.available_transition_statuses(status):
                raise TransitionNotRegistered
            # если заявке было выделено место или она окончательно зачислена, то сохраняем дату и время
            if self.status == STATUS_DECISION:
                self.decision_datetime = datetime.datetime.now()
            elif self.status == STATUS_DISTRIBUTED:
                self.distribution_datetime = datetime.datetime.now()
            # сохраняем дату и время последнего изменения статуса
            self.status_change_datetime = datetime.datetime.now()
        super(Requestion, self).save(*args, **kwargs)
        if not self.requestion_number:
            self.requestion_number = self.get_requestion_number()

            self.save()

    def clean(self):
        from django.core.exceptions import ValidationError
        if (self.birth_date and self.registration_datetime and
            self.birth_date > self.registration_datetime.date()):
            raise ValidationError(u'Дата регистрации не может быть меньше даты рождения')

    def available_transitions(self):
        from sadiki.core.workflow import workflow
        return [workflow.get_transition_by_index(ti)
                for ti in workflow.available_transitions(src=self.status)]

    def embed_requestion_to_profile(self, profile, user, reason):
        from sadiki.logger.models import Logger
        from sadiki.core.workflow import EMBED_REQUESTION_TO_PROFILE
        self.profile = profile
        self.save()
        Logger.objects.create_for_action(
            EMBED_REQUESTION_TO_PROFILE,
            extra={'user': user, 'obj': self, 'profile': profile},
            reason=reason)

    def geocode_address(self, geocoder_class):
        geocoder = geocoder_class()
        if settings.REGION_NAME:
            address = "%s, %s" % (settings.REGION_NAME, self.location_properties)
        else:
            address = self.location_properties
        coords = geocoder.geocode(address)
        return coords

    def set_location(self, coords):
        coords = map(float, coords)
        self.location = Point(*coords, srid=4326)

    def __unicode__(self):
        return self.requestion_number


class Area(models.Model):

    class Meta:
        verbose_name = u'территориальная область'
        verbose_name_plural = u'территориальная область'

    name = models.CharField(verbose_name=u"Название", max_length=100)
    ocato = models.CharField(verbose_name=u'ОКАТО', max_length=11,)
    # Cache
    bounds = PolygonField(verbose_name=u'Границы области', blank=True, null=True)

    def __unicode__(self):
        return self.name

    objects = GeoManager()

PREFERENCE_SECTION_MUNICIPALITY = "municipality"
PREFERENCE_SECTION_SYSTEM = "system"
PREFERENCE_SECTION_HIDDEN = "hidden"

PREFERENCE_SECTION_CHOICES = (
    (PREFERENCE_SECTION_MUNICIPALITY, u"Раздел с параметрами муниципалитета"),
    (PREFERENCE_SECTION_SYSTEM, u"Системные настройки"),
    (PREFERENCE_SECTION_HIDDEN,
        u"Настройки, которые могут изменяться только системой"),
)

# параметры муниципалитета
PREFERENCE_MUNICIPALITY_NAME = "MUNICIPALITY_NAME"
PREFERENCE_MUNICIPALITY_NAME_GENITIVE = "MUNICIPALITY_NAME_GENITIVE"
PREFERENCE_MUNICIPALITY_PHONE = "MUNICIPALITY_PHONE"
PREFERENCE_LOCAL_AUTHORITY = "LOCAL_AUTHORITY"
PREFERENCE_AUTHORITY_HEAD = "AUTHORITY_HEAD"

# парамтры системы
PREFERENCE_EMAIL_KEY_VALID = "EMAIL_KEY_VALID"

# настройки, изменяемые системой
PREFERENCE_IMPORT_FINISHED = "IMPORT_STATUS_FINISHED"
PREFERENCE_REQUESTIONS_IMPORTED = "REQUESTIONS_IMPORTED"

PREFERENCE_CHOICES = (
    (PREFERENCE_MUNICIPALITY_NAME, u'Название муниципалитета'),
    (PREFERENCE_MUNICIPALITY_NAME_GENITIVE, u'Название муниципалитета (родительный падеж)'),
    (PREFERENCE_MUNICIPALITY_PHONE, u'Контактный телефон'),
    (PREFERENCE_EMAIL_KEY_VALID, u'Срок действия ключа для подтверждения почты(дней)'),
    (PREFERENCE_IMPORT_FINISHED, u'Статус завершения импорта'),
    (PREFERENCE_REQUESTIONS_IMPORTED, u'Были импортированы заявки'),
    (PREFERENCE_LOCAL_AUTHORITY, u"""Наименование органа местного самоуправления, 
        осуществляющего управление в сфере образования (родительный падеж)"""),
    (PREFERENCE_AUTHORITY_HEAD, u"""ФИО главы органа местного самоуправления,
        осуществляющего управление в сфере образования (дательный падеж)"""),
)

PREFERENCES_MAP = {
    PREFERENCE_SECTION_MUNICIPALITY: [
        PREFERENCE_MUNICIPALITY_NAME,
        PREFERENCE_MUNICIPALITY_NAME_GENITIVE,
        PREFERENCE_MUNICIPALITY_PHONE,
        PREFERENCE_LOCAL_AUTHORITY,
        PREFERENCE_AUTHORITY_HEAD
    ],
    PREFERENCE_SECTION_SYSTEM: [PREFERENCE_EMAIL_KEY_VALID],
    PREFERENCE_SECTION_HIDDEN: [PREFERENCE_IMPORT_FINISHED, PREFERENCE_REQUESTIONS_IMPORTED],
}


class PreferenceQuerySet(models.query.QuerySet):

    def get_or_none(self, *args, **kwargs):
        try:
            object = self.get(*args, **kwargs)
        except Preference.DoesNotExist:
            object = None
        return object


class Preference(models.Model):
    class Meta:
        verbose_name = u"Параметр"
        verbose_name_plural = u"Параметры"

    section = models.CharField(verbose_name=u"Раздел", max_length=255,
        choices=PREFERENCE_SECTION_CHOICES)
    key = models.CharField(verbose_name=u"Ключ", max_length=255, unique=True,
        choices=PREFERENCE_CHOICES)
    datetime = models.DateTimeField(
        verbose_name=u"Дата и время последнего изменения")
    value = models.CharField(verbose_name=u"Значение", max_length=255)
    objects = query_set_factory(PreferenceQuerySet)

    def save(self, *args, **kwargs):
#        смотрим к какому разделу относится ключ
        for section, section_name in PREFERENCE_SECTION_CHOICES:
            if self.key in PREFERENCES_MAP[section]:
                self.section = section
                self.datetime = datetime.datetime.now()
                super(Preference, self).save(*args, **kwargs)
                return
#        если нет информации о разделе, то ошибка
        raise KeyError(u"Не указано к какому разделу относится ключ %s" % self.key)

    def __unicode__(self):
        return self.value


class ChunkCustom(Chunk):
    class Meta:
        proxy = True
        verbose_name = u'Блок на странице'
        verbose_name_plural = u'Блоки на странице'

    def __init__(self, *args, **kwargs):
        self._meta.get_field('key').verbose_name = u'Ключ'
        self._meta.get_field('content').verbose_name = u'Содержимое'
        self._meta.get_field('description').verbose_name = u'Описание'
        super(ChunkCustom, self).__init__(*args, **kwargs)


class UserFunctions:

    def is_operator(self):
        from sadiki.core.permissions import OPERATOR_PERMISSION
        return self.has_perm("auth.%s" % OPERATOR_PERMISSION[0])

    def is_requester(self):
        from sadiki.core.permissions import REQUESTER_PERMISSION
        return self.has_perm("auth.%s" % REQUESTER_PERMISSION[0])

    def is_administrator(self):
        from sadiki.core.permissions import ADMINISTRATOR_PERMISSION
        return self.has_perm("auth.%s" % ADMINISTRATOR_PERMISSION[0])

    def is_supervisor(self):
        from sadiki.core.permissions import SUPERVISOR_PERMISSION
        return self.has_perm("auth.%s" % SUPERVISOR_PERMISSION[0])

    def is_sadik_operator(self):
        from sadiki.core.permissions import SADIK_OPERATOR_PERMISSION
        return self.has_perm("auth.%s" % SADIK_OPERATOR_PERMISSION[0])

    def is_administrative_person(self):
        u"""
        является ли пользователь администратором, оператором или супервайзером
        """
        return any((self.is_operator(), self.is_sadik_operator(), self.is_administrator(),
            self.is_supervisor()))

    def perms_for_area(self, areas):
        u"""Есть ли у пользователя права на какую-нибудь из областей"""
        if isinstance(areas, Area):
            areas = (areas,)
        try:
            user_area = self.get_profile().area
        except Profile.DoesNotExist:
            return False
        else:
            return (user_area is None) or not areas or (user_area in areas)

    def email_busy(self):
        return bool(get_user_by_email(self.email))

    def get_verbose_name(self):
        u"""возвращает имя отчество пользователя с учетом типа учетки"""
        try:
            profile = self.get_profile()
        except Profile.DoesNotExist:
            pass
        else:
            if profile.nickname:
                return profile.nickname
#        если не смогли получить имя отчество у профиля, то берем их у пользователя
        if self.first_name or self.last_name:
            return u'%s %s' % (self.first_name or u'', self.last_name or u'')
        else:
            return self.username

    def set_username_by_id(self):
        username = "%s_%d" % (REQUESTER_USERNAME_PREFIX, self.id)
        new_username = username
        while User.objects.filter(username=new_username).exists():
            new_username = "%s_%s" % (username, random.randrange(1,999))
        self.username = new_username


def update_benefit_category(action, instance, **kwargs):
    u"""При изменении льгот у заявки обновляется поле benefit_category"""
    if action in ("post_add", "post_remove", "post_clear"):
#        получаем список категорий в зависимости от льгот(более приоритетные впереди)
        categories = BenefitCategory.objects.filter(
            benefit__requestion=instance).order_by('-priority')
        if categories:
            benefit_category = categories[0]
        else:
#            если не заданы льготы, то берем наименее приоритетную категорию
            benefit_category = BenefitCategory.objects.category_without_benefits()
        if instance.benefit_category != benefit_category:
            instance.benefit_category = benefit_category
            instance.save()

m2m_changed.connect(update_benefit_category, sender=Requestion.benefits.through)

User.__bases__ += (UserFunctions,)

del User.get_absolute_url

add_introspection_rules([], ["^sadiki\.core\.fields\.BooleanNextYearField"])
add_introspection_rules([], ["^sadiki\.core\.fields\.YearChoiceField"])
add_introspection_rules([], ["^sadiki\.core\.fields\.SplitDayMonthField"])
