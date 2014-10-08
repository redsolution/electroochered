# -*- coding: utf-8 -*-
from django.templatetags.static import static
import re
from attachment.admin import AttachmentImageInlines
from attachment.forms import AttachmentImageForm
from chunks.models import Chunk
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.contrib.gis.forms.fields import GeometryField
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models.query_utils import Q
from django.forms.widgets import CheckboxSelectMultiple
from django.template.response import TemplateResponse
from django.utils import six
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from sadiki.core.admin import CustomGeoAdmin
from sadiki.core.geo_field import map_widget, location_errors
from sadiki.core.models import BENEFIT_DOCUMENT, AgeGroup, Sadik, Address, \
    EvidienceDocumentTemplate, Profile, Benefit, BenefitCategory, Area, Distribution, \
    Preference, PREFERENCE_SECTION_MUNICIPALITY, PREFERENCES_MAP, District, \
    ChunkCustom
from sadiki.core.permissions import OPERATOR_GROUP_NAME, DISTRIBUTOR_GROUP_NAME, \
    SUPERVISOR_GROUP_NAME, SADIK_OPERATOR_GROUP_NAME, ADMINISTRATOR_GROUP_NAME, \
    SUPERVISOR_PERMISSION, OPERATOR_PERMISSION, SADIK_OPERATOR_PERMISSION, \
    ADMINISTRATOR_PERMISSION
from sadiki.core.settings import BENEFIT_SYSTEM_MIN, IMMEDIATELY_DISTRIBUTION_NO, \
    WITHOUT_BENEFIT_PRIORITY
import urllib
import urlparse

csrf_protect_m = method_decorator(csrf_protect)


def clean_str(text):
    text = re.sub("\n", ' ', text)
    text = re.sub("\s\s+", ' ', text)
    return text.strip()


def add_get_params_to_url(url, params=None):
    if params is None:
        params = {}
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(url_parts)


class CustomRelatedFieldWidgetWrapper(RelatedFieldWidgetWrapper):

    def __init__(self, get_params, *args, **kwargs):
        self.get_params = get_params
        super(CustomRelatedFieldWidgetWrapper, self).__init__(*args, **kwargs)

    def render(self, name, value, *args, **kwargs):
        rel_to = self.rel.to
        info = (rel_to._meta.app_label, rel_to._meta.object_name.lower())
        try:
            related_url = reverse('admin:%s_%s_add' % info, current_app=self.admin_site.name)
        except NoReverseMatch:
            info = (self.admin_site.root_path, rel_to._meta.app_label, rel_to._meta.object_name.lower())
            related_url = '%s%s/%s/add/' % info
        related_url = add_get_params_to_url(related_url, self.get_params)
        self.widget.choices = self.choices
        output = [self.widget.render(name, value, *args, **kwargs)]
        if self.can_add_related:
            # TODO: "id_" is hard-coded here. This should instead use the correct
            # API to determine the ID dynamically.
            output.append(u'<a href="%s" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);"> ' % \
                          (related_url, name))
            output.append(u'<img src="%s" width="10" height="10" alt="%s"/></a>'
                          % (static('admin/img/icon_addlink.gif'), _('Add Another')))
        return mark_safe(u''.join(output))


class AddressForm(forms.ModelForm):
    town = forms.CharField(label=u"Населенный пункт", max_length=255, required=False)
    block_number = forms.CharField(label=u'№ квартала', max_length=255, required=False)
    postindex = forms.IntegerField(label=u"Почтовый индекс", max_value=999999)
    street = forms.CharField(label=u"Улица", max_length=255)
    building_number = forms.CharField(label=u"Дом", max_length=255)

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.id:
            self.fields["town"].initial = self.instance.address.town
            self.fields["block_number"].initial = self.instance.address.block_number
            self.fields["postindex"].initial = self.instance.address.postindex
            self.fields["street"].initial = self.instance.address.street
            self.fields["building_number"].initial = self.instance.address.building_number

    def get_address(self, defaults=None):
        if defaults is None:
            defaults = {}
        return Address.objects.get_or_create(
                town = self.cleaned_data.get("town"),
                postindex=self.cleaned_data.get("postindex"),
                street=self.cleaned_data.get("street"),
                block_number = self.cleaned_data.get("block_number"),
                building_number=self.cleaned_data.get("building_number"),
                defaults=defaults)


class AddressWithMapForm(AddressForm):
    coords = GeometryField(label=u'Местоположение', geom_type="POINT")

    def __init__(self, *args, **kwargs):
        super(AddressWithMapForm, self).__init__(*args, **kwargs)
        self.fields["coords"].widget = map_widget()
        self.fields['coords'].error_messages.update(location_errors)
        if self.instance and self.instance.id:
            self.fields["coords"].initial = self.instance.address.coords

    def get_address(self):
        address, created = super(AddressWithMapForm, self).get_address(
            defaults={"coords": self.cleaned_data.get('coords')})
        if not created:
            address.coords = self.cleaned_data.get('coords')
            address.save()
        return address, created


class SadikiAdminSite(AdminSite):
    u"""класс изменяет проверку прав"""

    actions = []

    def __init__(self, name='sadik_admin', app_name='admin'):
        super(SadikiAdminSite, self).__init__(name, app_name)

    def has_permission(self, request):
        return request.user.is_active and request.user.is_administrator()

    @never_cache
    def index(self, request, extra_context=None):
        """
        Displays the main admin index page, which lists all of the installed
        apps that have been registered in this site.

        убрал проверку прав на модуль(в интерфейсе администратора нет разграничения прав)
        """
        app_dict = {}
        for model, model_admin in self._registry.items():
            app_label = model._meta.app_label
#            изменил: права всегда есть
            has_module_perms = True

            if has_module_perms:
                perms = model_admin.get_model_perms(request)

                # Check whether user has any perm for this module.
                # If so, add the module to the model_list.
                if True in perms.values():
                    info = (app_label, model._meta.module_name)
                    model_dict = {
                        'name': capfirst(model._meta.verbose_name_plural),
                        'perms': perms,
                    }
                    if perms.get('change', False):
                        try:
                            model_dict['admin_url'] = reverse('admin:%s_%s_changelist' % info, current_app=self.name)
                        except NoReverseMatch:
                            pass
                    if perms.get('add', False):
                        try:
                            model_dict['add_url'] = reverse('admin:%s_%s_add' % info, current_app=self.name)
                        except NoReverseMatch:
                            pass
                    if app_label in app_dict:
                        app_dict[app_label]['models'].append(model_dict)
                    else:
                        app_dict[app_label] = {
                            'name': app_label.title(),
                            'app_url': reverse('admin:app_list', kwargs={'app_label': app_label}, current_app=self.name),
                            'has_module_perms': has_module_perms,
                            'models': [model_dict],
                        }

        # Sort the apps alphabetically.
        app_list = list(six.itervalues(app_dict))
        app_list.sort(key=lambda x: x['name'])

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])

        context = {
            'title': _('Site administration'),
            'app_list': app_list,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, self.index_template or
                                'admin/index.html', context,
                                current_app=self.name)


site = SadikiAdminSite(name='sadiki_admin')

USER_TYPE_CHOICES = (
    (SUPERVISOR_PERMISSION[0], u'Суперпользователь'),
    (OPERATOR_PERMISSION[0], u'Оператор'),
    (ADMINISTRATOR_PERMISSION[0], u'Администратор'),
    )


def get_user_type(instance):
#    нельзя опираться на права пользователя, т.к. если он неактивен,
#    то у него нет прав. опираемся на группы
    groups_names = [group.name for group in instance.groups.all()]
    if SUPERVISOR_GROUP_NAME in groups_names:
        return SUPERVISOR_PERMISSION[0]
    elif OPERATOR_GROUP_NAME in groups_names:
        return OPERATOR_PERMISSION[0]
    elif SADIK_OPERATOR_GROUP_NAME in groups_names:
        return SADIK_OPERATOR_PERMISSION[0]
    elif ADMINISTRATOR_GROUP_NAME in groups_names:
        return ADMINISTRATOR_PERMISSION[0]


class OperatorAdminChangeForm(forms.ModelForm):
    user_type = forms.ChoiceField(label=u"Тип учетной записи",
        required=False, choices=USER_TYPE_CHOICES)

    class Meta:
        model = User

    def __init__(self, *args, **kwargs):
        super(OperatorAdminChangeForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['user_type'].initial = get_user_type(instance)


class OperatorAdminAddForm(OperatorAdminChangeForm):
    password1 = forms.CharField(widget=forms.PasswordInput,
        max_length=255, label=u'Пароль')
    password2 = forms.CharField(widget=forms.PasswordInput,
        max_length=255, label=u'Повторите пароль')

    def clean(self):
        cleaned_data = super(OperatorAdminAddForm, self).clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError(u'Пароли не совпадают')
        return cleaned_data

    def save(self, commit=True):
        user = super(OperatorAdminAddForm, self).save(commit=False)
        password1 = self.cleaned_data.get('password1')
        user.set_password(password1)
        if commit:
            user.save()
        return user


class ModelAdminWithoutPermissionsMixin(object):

    class Media:
        css = {
                 'all': ('css/admin_override.css',)
            }

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return self.has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


def verbose_user_type(obj):
    return dict(USER_TYPE_CHOICES)[get_user_type(obj)]
verbose_user_type.short_description = 'Тип учетной записи'


class UserAdmin(ModelAdminWithoutPermissionsMixin, UserAdmin):
    change_form_template = "adm/user/operator_change_template.html"
    fieldsets = (
        (None, {'fields': ['user_type', 'username', 'first_name', 'last_name',
        'is_active', 'is_staff']}),
    )
    add_fieldsets = (
        (None, {'fields': ['user_type', 'username', 'first_name', 'last_name',
        'is_staff', 'password1', 'password2']}),
    )
    add_form = OperatorAdminAddForm
    form = OperatorAdminChangeForm
    list_display = ('username', 'first_name', 'last_name', verbose_user_type)
    list_filter = ()

    class Media:
        css = {
                 'all': ('css/admin_override.css',)
            }

    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = super(UserAdmin, self).queryset(self)
        return qs.filter(groups__name__in=(
            OPERATOR_GROUP_NAME, SUPERVISOR_GROUP_NAME,
            SADIK_OPERATOR_GROUP_NAME, ADMINISTRATOR_GROUP_NAME)
            ).distinct()

    def save_model(self, request, obj, form, change):
        obj.save()
        try:
            obj.get_profile()
        except Profile.DoesNotExist:
            Profile.objects.create(user=obj)
#        список групп, которые нужно назначить пользователю
        user_groups = []
        supervisor_group = Group.objects.get(name=SUPERVISOR_GROUP_NAME)
        operator_group = Group.objects.get(name=OPERATOR_GROUP_NAME)
        sadik_operator_group = Group.objects.get(name=SADIK_OPERATOR_GROUP_NAME)
        administrator_group = Group.objects.get(name=ADMINISTRATOR_GROUP_NAME)
        distributor_group = Group.objects.get(name=DISTRIBUTOR_GROUP_NAME)
        user_type = form.cleaned_data.get('user_type')
        if user_type == SUPERVISOR_PERMISSION[0]:
#        если супервайзер
            user_groups.append(supervisor_group)
        elif user_type == OPERATOR_PERMISSION[0]:
#        если оператор
            user_groups.append(operator_group)
            user_groups.append(distributor_group)
            user_groups.append(sadik_operator_group)
        elif user_type == ADMINISTRATOR_PERMISSION[0]:
#        если администратор
            user_groups.append(administrator_group)
        obj.groups = user_groups


class AreaAdminForm(forms.ModelForm):
    model = Sadik

    def clean_name(self):
        return clean_str(self.cleaned_data.get('name'))


class AreaAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):
    model = Area
    form = AreaAdminForm
    fields = ['name', 'ocato', 'district']

    def clean_name(self):
        return clean_str(self.cleaned_data.get('name'))


class SadikAdminForm(AddressWithMapForm, forms.ModelForm):

    class Meta:
        model = Sadik

    def __init__(self, *args, **kwargs):
        self.base_fields['age_groups'].widget = CheckboxSelectMultiple()
        self.base_fields['age_groups'].initial = AgeGroup.objects.all(
            ).values_list('id', flat=True)
        self.base_fields['age_groups'].required=False
        super(SadikAdminForm, self).__init__(*args, **kwargs)
        self.fields['age_groups'].help_text = u"""Возрастные группы,
        которые могут быть в ДОУ. Учитываются при переводе групп ДОУ
        в новый учебный год"""

    def clean_active_distribution(self):
        active_distribution = self.cleaned_data.get("active_distribution")
        if 'active_distribution' in self.changed_data:
            if not active_distribution and Distribution.objects.active():
                raise forms.ValidationError(
                    u"Во время распределения нельзя запретить зачисление в ДОУ")
        return active_distribution

    def clean_identifier(self):
        return clean_str(self.cleaned_data.get('identifier'))


class SadikAdmin(ModelAdminWithoutPermissionsMixin, CustomGeoAdmin):

    form = SadikAdminForm
    model = Sadik
    fields = ('area', 'name', 'short_name', 'identifier', 'town', 'postindex',
        'block_number', 'street',
        'building_number', 'coords', 'email', 'site',
        'head_name', 'phone', 'cast', 'tech_level', 'training_program',
        'route_info', 'extended_info', 'active_registration',
        'active_distribution', 'age_groups',)
    list_display = ['name', 'identifier']
    raw_id_fields = ['address']

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        address, created = form.get_address()
        obj.address = address
        obj.save()


class EvidienceDocumentTemplateAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):
    model = EvidienceDocumentTemplate
    list_display = ['name', 'destination']


benefit_category_query = (Q(priority__lt=BENEFIT_SYSTEM_MIN) &
    ~Q(priority=WITHOUT_BENEFIT_PRIORITY))


class BenefitCategoryAdminForm(forms.ModelForm):
    class Meta:
        model = BenefitCategory
        if settings.IMMEDIATELY_DISTRIBUTION == IMMEDIATELY_DISTRIBUTION_NO:
            exclude = ('immediately_distribution_active',)

    def clean_priority(self):
        priority = self.cleaned_data.get('priority')
        other_categories = BenefitCategory.objects.filter(priority=priority)
        if self.instance.id:
            other_categories = other_categories.exclude(id=self.instance.id)
        if other_categories.exists():
            raise forms.ValidationError(u"Такой приоритет уже используется")
        else:
            return priority


class BenefitCategoryAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):
    model = BenefitCategory
    form = BenefitCategoryAdminForm
    list_display = ['name', 'priority']

    def queryset(self, request):
#        исключаем системные льготы и категорию "Без льгот"
        qs = super(BenefitCategoryAdmin, self).queryset(request)
        return qs.filter(benefit_category_query)


class BenefitAdminForm(forms.ModelForm):
    class Meta:
        model = Benefit

    def __init__(self, *args, **kwargs):
        super(BenefitAdminForm, self).__init__(*args, **kwargs)
        self.fields["category"].queryset = BenefitCategory.objects.filter(
            benefit_category_query)
        # добавление GET параметров к url для добавления элемента(мы хотим, чтобы передавался тип документов для льгот)
        # более элегантного решения не придумал
        self.fields["evidience_documents"].widget = CustomRelatedFieldWidgetWrapper(
            {"destination": BENEFIT_DOCUMENT},
            Benefit._meta.get_field('evidience_documents').formfield().widget,
            Benefit._meta.get_field('evidience_documents').rel,
            site, can_add_related=True)
        self.fields["evidience_documents"].queryset = EvidienceDocumentTemplate.objects.filter(
            destination=BENEFIT_DOCUMENT)

    def clean_name(self):
        return clean_str(self.cleaned_data.get('name'))


class BenefitAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):
    model = Benefit
    form = BenefitAdminForm
    exclude = ('sadik_related',)
    list_display = ['name', 'category']

    def queryset(self, request):
        return Benefit.objects.list()


class AgeGroupForm(forms.ModelForm):
    sadiks = forms.ModelMultipleChoiceField(label=u"ДОУ в которых есть группа",
        queryset=Sadik.objects.all(), widget=CheckboxSelectMultiple(),
        required=False)

    class Meta:
        model = AgeGroup

    def __init__(self, *args, **kwargs):
        super(AgeGroupForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['sadiks'].initial = self.instance.sadik_set.all()
        else:
            self.fields['sadiks'].initial = Sadik.objects.all()

    def clean_name(self):
        return clean_str(self.cleaned_data.get('name'))

    def clean_short_name(self):
        return clean_str(self.cleaned_data.get('short_name'))

    def clean(self):
        from_age = self.cleaned_data.get('from_age')
        to_age = self.cleaned_data.get('to_age')
        if (from_age and to_age and from_age >= to_age):
            raise forms.ValidationError(
                u"Минимальный возраст должен быть меньше максимального")
        return self.cleaned_data

    def save(self, commit=True):
        instance = super(AgeGroupForm, self).save(commit=False)
        _save_m2m = self.save_m2m
        def save_m2m():
            _save_m2m()
            self.instance.sadik_set = self.cleaned_data.get('sadiks')
        if commit:
            instance.save()
            save_m2m()
        else:
            self.save_m2m = save_m2m
        return instance


class AgeGroupAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):
    model = AgeGroup
    form = AgeGroupForm
    list_display = ['__unicode__', 'next_age_group']


class ChunkAdminForm(forms.ModelForm):
    class Meta:
        model = Chunk

    def __init__(self, *args, **kwargs):
        super(ChunkAdminForm, self).__init__(*args, **kwargs)
        self.fields['key'].label = u'Ключ'
        self.fields['key'].help_text = None
        self.fields['content'].label = u'Содержимое'
        self.fields['description'].label = u'Описание'


class AttachmentImageFormCustom(AttachmentImageForm):

    class Meta:
        fields = ('image',)


class DistrictAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):
    search_fields = ('title', )


class AttachmentImageInlinesCustom(AttachmentImageInlines):
    form = AttachmentImageFormCustom

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return self.has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


class ChunkAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):

    model = ChunkCustom
    inlines = [AttachmentImageInlinesCustom, ]
    list_display = ['key', 'description']


class PreferenceAdminForm(forms.ModelForm):
    class Meta:
        model = Preference

    def __init__(self, *args, **kwargs):
        available_choices = []
        for section in [PREFERENCE_SECTION_MUNICIPALITY, ]:
            available_choices += PREFERENCES_MAP[section]
        self.base_fields['key'].choices = (choice for choice in  self.base_fields['key'].choices
            if choice[0] in available_choices)
        super(PreferenceAdminForm, self).__init__(*args, **kwargs)


class PreferenceAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):
    model = Preference
    fields = ('key', 'value')
    list_display = ['key', 'section', 'value']
    form = PreferenceAdminForm

    def queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = super(PreferenceAdmin, self).queryset(self)
        return qs.filter(section=PREFERENCE_SECTION_MUNICIPALITY)


site.register(User, UserAdmin)
site.register(Sadik, SadikAdmin)
site.register(Area, AreaAdmin)
site.register(EvidienceDocumentTemplate, EvidienceDocumentTemplateAdmin)
site.register(AgeGroup, AgeGroupAdmin)
site.register(BenefitCategory, BenefitCategoryAdmin)
site.register(Benefit, BenefitAdmin)
site.register(ChunkCustom, ChunkAdmin)
site.register(Preference, PreferenceAdmin)
site.register(District, DistrictAdmin)
