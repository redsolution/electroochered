# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.template.loader import render_to_string
from sadiki.administrator.import_plugins import INSTALLED_FORMATS, \
    SADIKS_FORMATS
from sadiki.administrator.utils import get_xlwt_style_list
from sadiki.core.importpath import importpath
from sadiki.core.models import Requestion, Sadik, Address
from sadiki.core.utils import get_unique_username
from xlutils.copy import copy
import datetime
import os
import tempfile
import xlrd
import xlwt


class Photo(models.Model):
    name = models.CharField(verbose_name=u'название', max_length=255)
    description = models.CharField(verbose_name=u'описание', max_length=255,
        blank=True, null=True)
    image = models.ImageField(verbose_name=u'фотография',
        upload_to='upload/sadik/images/', blank=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

TABLE_TYPE_CHOICES = (
    (0, u'Очередники'),
    (1, u'Первоочередники'),
    (2, u'Внеочередники'),
)

#===============================================================================
# Импорт данных
#===============================================================================

min_birth_date = lambda: datetime.date.today().replace(
    year=datetime.date.today().year - settings.MAX_CHILD_AGE)

class CellParserMismatch(Exception):

    def __init__(self):
        self.messages = [u'Неверный тип поля', ]

class ErrorRow(list):

    def __init__(self, data, index, logic_exception=None):
        self.row_index = index
        self.logic_exception = logic_exception
        super(ErrorRow, self).__init__(data)

class CellParser(object):
    parser_type = None

    def __init__(self, value, datemode):
        self.value = value
        self.datemode = datemode

    def to_python(self):
        """return python object or raise ValidationError"""
        raise NotImplementedError('Override this method in children class')

class Format(object):

    cells = []  # override this

    # xls reading options
    start_line = 0
    sheet_num = 0

    def __init__(self, document, name=None):
        """
        name - internal format name
        cell_parser - iterable object, contains row cells for validation
        for example:
            [(cell1,),
             (cell2,),
             (cell3_1, cell3_2),
             (cell4,)]
        If validation in cell3_1 fails, format will try to validate cell3_2.
        """
        self.name = name
        self.document = document
        self.cell_data = []
        self.sheet = self.document.sheet_by_index(self.sheet_num)

    def to_python(self, data_row):
        """
        Returns python object with all required data
        Object should not expect any Exception subclasses in data_row
        Should return tuple of objects:
            requestion, profile, sadik_number_list
        """
        raise NotImplementedError('Override this method in children class')

    def _run_cell_parser(self, cell_parser, cell_data):
        """Validate cell data through parser"""
        if cell_parser.parser_type == cell_data.ctype:
            return cell_parser(cell_data.value, self.document.datemode).to_python()
        else:
            raise CellParserMismatch()

    def __iter__(self):
        return self.next()

    def next(self):
        # per-row validation
        for rownum in range(self.start_line, self.sheet.nrows):
            data_row = self.sheet.row_slice(rownum)[:len(self.cells)]
            parsed_data = []

            # per-cell validation
            for i, cell_data in enumerate(data_row):
                # temp variables
                exception = None
                value = None
                ok = False  # bool if any value returned
                # run all parsers
                for cell_parser in self.cells[i]['parsers']:
                    try:
                        value = self._run_cell_parser(cell_parser, cell_data)
                        ok = True
                        break
                    except ValidationError, e:
                        if exception is None:
                            exception = e
                        else:
                            pass  # go to next cellparser
                    except CellParserMismatch:
                        pass  # go to next cellparser

                # store value and exception data
                if (not ok) and (exception is None):
                    exception = CellParserMismatch()
                if ok:
                    parsed_data.append(value)
                else:
                    parsed_data.append(exception)

            yield parsed_data

def validate_fields_length(obj):
    u"""
    проверяем, что длина строки не превышает макс. длины поля
    """
    errors = []
    for field in obj._meta.fields:
        if (all((field.max_length, field.value_from_object(obj))) and
            len(field.value_from_object(obj)) > field.max_length):
            errors.append(u'В поле "%s" должно быть не больше %d символов' %
                (field.verbose_name, field.max_length))
    return errors

#def validate_object(obj):
#    errors=[]
#    try:
#        obj.full_clean()
#    except ValidationError as e:
#        for key, error_messages in e.message_dict.iteritems():
#            if key != NON_FIELD_ERRORS:
#                errors.append("%s: %s" % (obj._meta.get_field_by_name(key)[0].verbose_name,
#                                          ";".join([error_message for error_message in error_messages])))
#            else:
#                errors.append([error_message for error_message in error_messages])
#    return errors



class RequestionLogic(object):

    def __init__(self, format_doc, fake=False):
        """
        Describes main buisness logic in import process
        format_doc - instance of subclass of Format
        """
        self.format_doc = format_doc
        self.errors = []
        self.fake = fake

    def validate(self):
        """
        Run through cells, if cell is valid, store python value,
        if not - store error information
        """
        for index, parsed_row in enumerate(self.format_doc):
            if any([issubclass(type(cell), Exception) for cell in parsed_row]):
                self.errors.append(ErrorRow(parsed_row, index +
                    self.format_doc.start_line))
            else:
                try:
                    self.validate_record(self.format_doc.to_python(parsed_row))
                except ValidationError, e:
                    self.errors.append(ErrorRow(parsed_row,
                        index + self.format_doc.start_line, e))

    def validate_record(self, data_tuple):
        from sadiki.core.workflow import REQUESTION_IMPORT
        from sadiki.core.workflow import IMPORT_PROFILE
        requestion, profile, areas, sadik_number_list, address_data, benefits, document = data_tuple
        errors = []
        address = Address.objects.get_or_create(**address_data)[0]
        requestion.address = address
        requestion.profile = profile
#        если у заявки не указано время регистрации, то устанавливаем 9:00
        if type(requestion.registration_datetime) is datetime.date:
            requestion.registration_datetime = datetime.datetime.combine(
                requestion.registration_datetime, datetime.time(9, 0))
        requestion = self.change_registration_datetime_coincedence(requestion)
        try:
            self.validate_duplicate(requestion)
        except ValidationError, e:
            errors.extend(e.messages)
        try:
            self.validate_registration_date(requestion)
        except ValidationError, e:
            errors.extend(e.messages)
        try:
            self.validate_dates(requestion)
        except ValidationError, e:
            errors.extend(e.messages)
        try:
            preferred_sadiks = self.validate_sadik_list(requestion, areas, sadik_number_list)
        except ValidationError, e:
            errors.extend(e.messages)
        try:
            self.validate_admission_date(requestion)
        except ValidationError, e:
            errors.extend(e.messages)
        length_errors = []
        length_errors.extend(validate_fields_length(address))
        length_errors.extend(validate_fields_length(profile))
        length_errors.extend(validate_fields_length(requestion))
        length_errors.extend(validate_fields_length(document))
        if length_errors:
            errors.extend(length_errors)
        if errors:
            raise ValidationError(errors)
        else:
#            ошибок нет, можно сохранять объекты
            if not self.fake:
                user = User.objects.create_user(get_unique_username(), '')
                permission = Permission.objects.get(codename=u'is_requester')
                user.user_permissions.add(permission)
                profile.user = user
                profile.save()
                address.save()
                requestion.profile = profile
                requestion.save()
                document.content_object = requestion
                document.save()
                if areas:
                    requestion.areas.add(*areas)
                for sadik in preferred_sadiks:
                    requestion.pref_sadiks.add(sadik)
#                добавляем льготы
                if benefits:
                    for benefit in benefits:
                        requestion.benefits.add(benefit)
                        requestion.save()
                context_dict = {'user': user, 'profile': profile,
                                'requestion': requestion,
                                'pref_sadiks': preferred_sadiks,
                                'areas': areas, 'benefits': benefits}
                from sadiki.logger.models import Logger
                Logger.objects.create_for_action(IMPORT_PROFILE,
                    context_dict={'user': user, 'profile': profile},
                    extra={'obj': profile})
                Logger.objects.create_for_action(REQUESTION_IMPORT,
                    context_dict=context_dict,
                    extra={'obj': requestion,
                        'added_pref_sadiks': preferred_sadiks})

    def validate_duplicate(self, requestion):
        if (all((requestion.first_name, requestion.last_name, requestion.patronymic)) and
            Requestion.objects.filter(first_name=requestion.first_name,
                last_name=requestion.last_name, patronymic=requestion.patronymic,
                birth_date=requestion.birth_date).count() > 0):
            raise ValidationError(u'Заявка уже встречается')
#
    def validate_registration_date(self, requestion):
        u"""заявки должны быть поданы до 1 марта 2011"""
        if datetime.date.today() <= requestion.registration_datetime.date():
            raise ValidationError(
                u'Дата регистрации не может быть больше текущей даты.')

    def validate_dates(self, requestion):
        u"""проверка, что дата рождения попадает в диапазон для зачисления и
        дата регистрации больше даты рождения"""
        if datetime.date.today() < requestion.birth_date or requestion.birth_date <= min_birth_date():
            raise ValidationError(u'Возраст ребёнка не подходит для зачисления в ДОУ.')
        if requestion.registration_datetime.date() < requestion.birth_date:
            raise ValidationError(u'Дата регистрации меньше даты рождения ребёнка.')

    def validate_sadik_list(self, requestion, areas, sadik_number_list):
        u"""проверяем, номера ДОУ"""
        errors = []
        preferred_sadiks = []
        if type(sadik_number_list) is list:
            for sadik_number in sadik_number_list:
                sadiks = Sadik.objects.filter(
                    number=sadik_number,)
                if areas:
                    sadiks = sadiks.filter(area__in=[area.id for area in areas])
                if sadiks.count() == 1:
                    preferred_sadiks.append(sadiks[0])
                elif not sadiks.count():
                    errors.append(
                        u'В данной территориальной области нет ДОУ с номером %s' % sadik_number)
                elif sadiks.count() >= 2:
                    errors.append(
                        u'В данной территориальной области есть несколько ДОУ с номером %s' % sadik_number)
        if errors:
            raise ValidationError(errors)
        else:
            return preferred_sadiks

    def validate_admission_date(self, requestion):
        if requestion.admission_date and (requestion.admission_date.year >
                datetime.date.today().year + settings.MAX_CHILD_AGE):
            raise ValidationError(u'Для желаемого года зачисления указано слишком большое значение.')

    def change_registration_datetime_coincedence(self, requestion):
        u"""Если для данного района уже есть заявка с такой датой и временем,то
            для данной заявки добавить 10 минут"""
#        если в районе есть заявки с такой же датой и временем регистрации
        if Requestion.objects.filter(
            registration_datetime=requestion.registration_datetime).count():
#            получаем последнюю заявку, поданную в этот день
            last_requestion = Requestion.objects.filter(
                registration_datetime__year=requestion.registration_datetime.year,
                registration_datetime__month=requestion.registration_datetime.month,
                registration_datetime__day=requestion.registration_datetime.day,
                ).order_by('-registration_datetime')[0]
            requestion.registration_datetime = last_requestion.registration_datetime + \
                datetime.timedelta(minutes=10)
        return requestion

    def save_xls_results(self, path_to_file):
        u"""в UPLOAD_ROOT создаётся файл с именем file_name в котором строки с ошибками красные"""
        rb = self.format_doc.document
        rb_sheet = rb.sheet_by_index(0)
        wb = copy(rb)
        ws = wb.get_sheet(0)
        styles = get_xlwt_style_list(rb)
        for error in self.errors:
            row = rb_sheet.row(error.row_index)
            style = xlwt.easyxf('pattern: pattern solid, fore_colour red; align: horiz centre, vert centre; borders: top thin, bottom thin, left thin, right thin;')
            for i, cell in enumerate(row):
                style.num_format_str = styles[cell.xf_index].num_format_str
                ws.write(error.row_index, i, cell.value, style)
        wb.save(path_to_file)

class SadikLogic(object):
    sadiks_identifiers = []
    errors = []

    def __init__(self, format_doc, area, fake=False):
        self.format_doc = format_doc
        self.area = area
        self.fake = fake

    def validate(self):
        for index, parsed_row in enumerate(self.format_doc):
            if any([issubclass(type(cell), Exception) for cell in parsed_row]):
                self.errors.append(ErrorRow(parsed_row, index +
                    self.format_doc.start_line))
            else:
                sadik_object, address_data, age_groups = self.format_doc.to_python(parsed_row)
                if sadik_object.number in self.sadiks_identifiers:
                    self.errors.append(ErrorRow(parsed_row,
                        index + self.format_doc.start_line, ValidationError(u'ДОУ с номером "%s" уже встречается' % sadik_object.number)))
                else:
                    self.sadiks_identifiers.append(sadik_object.identifier)
                self.import_sadik(sadik_object, address_data, age_groups)

    def import_sadik(self, sadik_obj, address_data, age_groups):
        if not self.fake:
            address = Address.objects.get_or_create(**address_data)[0]
            sadik_obj.address = address
            sadik_obj.save()
            sadik_obj.age_groups = age_groups

    def save_xls_results(self, path_to_file):
        u"""в UPLOAD_ROOT создаётся файл с именем file_name в котором строки с ошибками красные"""
        rb = self.format_doc.document
        rb_sheet = rb.sheet_by_index(0)
        wb = copy(rb)
        ws = wb.get_sheet(0)
        styles = get_xlwt_style_list(rb)
        for error in self.errors:
            row = rb_sheet.row(error.row_index)
            style = xlwt.easyxf('pattern: pattern solid, fore_colour orange; align: horiz centre, vert centre; borders: top thin, bottom thin, left thin, right thin;')
            for i, cell in enumerate(row):
                style.num_format_str = styles[cell.xf_index].num_format_str
                ws.write(error.row_index, i, cell.value, style)
        wb.save(path_to_file)

IMPORT_INITIAL = 0
IMPORT_START = 1
IMPORT_FINISH = 2
IMPORT_ERROR = 3

IMPORT_TASK_CHOICES = (
    (IMPORT_INITIAL, u"Обработка не начата"),
    (IMPORT_START, u"Обработка начата"),
    (IMPORT_FINISH, u"Обработка завершена"),
    (IMPORT_ERROR, u"Ошибка во время импорта"),
)


secure_static_storage = FileSystemStorage(
    location=settings.SECURE_STATIC_ROOT, base_url='/adm/administrator/importtask/')


class ImportTask(models.Model):

    class Meta:
        verbose_name = u'Файл с данными'
        verbose_name_plural = u'Файлы с данными'

    source_file = models.FileField(verbose_name=u'Файл с данными(в формате xls)',
        storage=secure_static_storage, upload_to=settings.IMPORT_STATIC_DIR)
    status = models.IntegerField(verbose_name=u"Статус", choices=IMPORT_TASK_CHOICES,
                                default=0)
    errors = models.IntegerField(verbose_name=u'Количество ошибок при импортировании',
        default=IMPORT_INITIAL)
    total = models.IntegerField(verbose_name=u'Количество записей', default=0)
    fake = models.BooleanField(verbose_name=u'Только проверка файла', default=True)
    data_format = models.CharField(verbose_name=u'Модуль импорта',
        choices=INSTALLED_FORMATS, max_length=250)
    result_file = models.FileField(verbose_name=u'Результат обработки',
        storage=secure_static_storage, upload_to=settings.IMPORT_STATIC_DIR,
        blank=True, null=True)
    file_with_errors = models.FileField(verbose_name=u'Список ошибок',
        storage=secure_static_storage, upload_to=settings.IMPORT_STATIC_DIR,
        blank=True, null=True)

    def delete(self, *args, **kwds):
        # Try to delete result file
        if self.result_file and os.path.exists(self.result_file):
            try:
                os.remove(self.result_file)
            except IOError:
                pass
        if self.file_with_errors and os.path.exists(self.file_with_errors):
            try:
                os.remove(self.file_with_errors)
            except IOError:
                pass
        return super(ImportTask, self).delete(*args, **kwds)

    def save_file_with_errors(self, context):
        new_filename, ext = os.path.splitext(os.path.basename(
                self.source_file.path))
        self.file_with_errors.name = os.path.join(
            self.file_with_errors.field.upload_to, new_filename + u'.html')
        file_with_errors = file(self.file_with_errors.path, "wb")
#        CreatePDF(render_to_string('administrator/import_errors.html',
#            context), file_with_errors)
        file_with_errors.write(render_to_string('administrator/import_errors.html',
            context).encode('utf-8'))
        file_with_errors.close()
        self.save()

    def process(self):
        # avoid cross-import
        FormatClass = importpath(self.data_format)
        source_file = open(self.source_file.path, 'r')
        descriptor, name = tempfile.mkstemp()
        os.fdopen(descriptor, 'wb').write(source_file.read())
        try:
            doc = xlrd.open_workbook(name, formatting_info=True)
        except xlrd.biffh.XLRDError:
            self.save_file_with_errors(
                {'error_message': u"Неверный тип файла. Для импорта необходимо использовать файлы формат xls",
                 'media_root': settings.MEDIA_ROOT})
            self.errors = 1
        else:
            format_doc = FormatClass(doc)
            if format_doc.sheet.ncols >= len(format_doc.cells):
                if self.data_format in SADIKS_FORMATS:
                    logic = SadikLogic(format_doc, None, self.fake)
                else:
                    logic = RequestionLogic(format_doc, self.fake)
                logic.validate()

                new_filename, ext = os.path.splitext(os.path.basename(
                    self.source_file.path))

                if not os.path.exists(os.path.join(settings.SECURE_STATIC_ROOT, self.file_with_errors.field.upload_to)):
                    os.mkdir(os.path.join(settings.SECURE_STATIC_ROOT, self.file_with_errors.field.upload_to))

                self.result_file.name = os.path.join(self.file_with_errors.field.upload_to,
                    new_filename + '_res' + ext)

                logic.save_xls_results(self.result_file.path)

                self.save_file_with_errors(
                    {'logic': logic, 'media_root': settings.MEDIA_ROOT})

                self.status = IMPORT_FINISH
                self.total = logic.format_doc.sheet.nrows - logic.format_doc.start_line
                self.errors = len(logic.errors)
                self.save()
                return logic
            else:
                self.save_file_with_errors(
                    {'error_message': u"Недостаточное количество столбцов",
                        'media_root': settings.MEDIA_ROOT})
                self.errors = 1
        self.status = IMPORT_FINISH
        self.save()

    def __unicode__(self):
        return u'Файл с данными %s' % self.get_data_format_display()
