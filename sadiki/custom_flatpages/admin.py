# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.flatpages.models import FlatPage
from sadiki.administrator.admin import site, ModelAdminWithoutPermissionsMixin
from trustedhtml.widgets import TrustedTinyMCE

PAGE_TYPE_CHOICES = (
    ("/about_registration/", u"Зачем регистрироваться в системе"),
    ("/queue_howto/", u"Как смотреть очередь"),
    ("/about/", u"О проекте"),
    ("/contacts/", u"Контактная информация"),
    )

TEMPLATES_FOR_URLS = {
    "/about_registration/": "flatpages/about_registration.html",
    "/queue_howto/": "flatpages/queue_howto.html",
    "/about/": "flatpages/about.html",
    }


class FlatPageForm(forms.ModelForm):
    url = forms.ChoiceField(label=u"Тип страницы", choices=PAGE_TYPE_CHOICES)
    content = forms.CharField(label=u"Содержимое", widget=TrustedTinyMCE(attrs={'cols': 80, 'rows': 30}))

    class Meta:
        model = FlatPage
        fields = '__all__'

    def clean_url(self):
        url = self.cleaned_data.get('url')
        pages = FlatPage.objects.filter(url=url)
        if self.instance.id:
            pages = pages.exclude(id=self.instance.id)
        if pages.exists():
            raise forms.ValidationError(u'Страница с таким типом уже создана')
        else:
            return url

    def save(self, commit=True):
        page = super(FlatPageForm, self).save(commit=False)
        if page.url in TEMPLATES_FOR_URLS:
            template_name = TEMPLATES_FOR_URLS[page.url]
        else:
            template_name = "flatpages/default.html"
        page.template_name = template_name
        if commit:
            page.save()
        return page


class FlatPageAdmin(ModelAdminWithoutPermissionsMixin, admin.ModelAdmin):
    form = FlatPageForm
    fields = ('url', 'title', 'content', 'sites')
    list_display = ('page_type', 'url', 'title')
    list_filter = ('sites', 'enable_comments', 'registration_required')
    search_fields = ('url', 'title')

    def page_type(self, obj):
        return dict(PAGE_TYPE_CHOICES)[obj.url]

    page_type.short_description = u"Тип страницы"

try:
    site.unregister(FlatPage)
except NotRegistered:
    pass

site.register(FlatPage, FlatPageAdmin)
