# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe
import re
from django.utils.text import capfirst
from classytags.arguments import Argument, MultiKeywordArgument
from classytags.core import Options, Tag
from classytags.helpers import InclusionTag
from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.wsgi import WSGIRequest
from django.core.urlresolvers import resolve, NoReverseMatch, Resolver404, \
    reverse
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.test.client import FakePayload
from django.utils.http import urlencode
from django.utils.importlib import import_module
from sadiki.core.models import AgeGroup, BenefitCategory

register = template.Library()

@register.filter
def element_by_index(sequence, index):
    u"""возвращает элемент с индексом index"""
    return sequence[index]

@register.filter
def verbose_value(value):
    verbose_values_dict = {
                u'': u'Не задано',
                None: u'Не задано',
                True: u'Да',
                False: u'Нет'
            }
    if value in verbose_values_dict:
        return verbose_values_dict[value]
    else:
        return value

@register.simple_tag()
def raw_include(template_name):
    # This code copied from django.template.loader
    loaders = []
    for path in settings.TEMPLATE_LOADERS:
        i = path.rfind('.')
        module, attr = path[:i], path[i + 1:]
        try:
            mod = import_module(module)
        except ImportError, e:
            raise ImproperlyConfigured, 'Error importing template source loader %s: "%s"' % (module, e)
        try:
            func = getattr(mod, attr)
        except AttributeError:
            raise ImproperlyConfigured, 'Module "%s" does not define a "%s" callable template source loader' % (module, attr)
        if not func.is_usable:
            import warnings
            warnings.warn("Your TEMPLATE_LOADERS setting includes %r, but your Python installation doesn't support that type of template loading. Consider removing that line from TEMPLATE_LOADERS." % path)
        else:
            loaders.append(func)

    for loader in loaders:
        try:
            source, _ = loader().load_template_source(template_name)
        except TemplateDoesNotExist:
            continue
        else:
            return source
    raise TemplateDoesNotExist, template_name

class FakeWSGIRequest(WSGIRequest):

    def __init__(self, environ):
        super(FakeWSGIRequest, self).__init__(environ)
        self.META['IS_FAKE'] = True


@register.filter
def check_url_availability(url, user):
    func = resolve(url)
    request = FakeWSGIRequest({
        'REQUEST_METHOD': 'HEAD',
        'wsgi.input': FakePayload(''),
    })
    request.user = user
    return func.func(request, *func.args, **func.kwargs)


class CheckUrlAvailability(Tag):
    options = Options(
        Argument('url', required=True),
        'as',
        Argument('varname', required=True, resolve=False)
    )

    def render_tag(self, context, url, varname):
        result = check_url_availability(url, context["user"])
        context[varname] = result
        return ''

register.tag(CheckUrlAvailability)


class ActionButtonForUrl(InclusionTag):
    u"""
    Производится проверка может ли выполняться вьюха,
    по результатам отображается ссылка и может быть возвращен результат
    доступности
    {% action_button_for_url url [get_params par1 = 1 par2 = 2]
        [options text = "text" hide_disabled = 1] [result result_var] %}
    """

    template = "core/template_tags/action_button_for_url.html"
    options = Options(
        Argument('url'),
        'get_params',
        MultiKeywordArgument('get_params', resolve=True, required=False),
        'options',
        MultiKeywordArgument('options', required=False),
        'result',
        Argument('varname', resolve=False, required=False),
        )

    def get_context(self, context, url, get_params, options, varname):
        result = check_url_availability(url, context['user'])
        if varname:
            context[varname] = result
        if get_params:
            url = "%s?%s" % (url, urlencode(get_params))
        return {'available': result, 'url': url, 'options': options}

register.tag(ActionButtonForUrl)

@register.tag
def create_extend_list(parser, token):
    u"""
    создает список из переданных элементов(для списков выполняется extend)
    create_list item [item item ...] as varname
    """
    bits = list(token.split_contents())
    if len(bits) > 3 and bits[-2] == 'as':
        varname = bits[-1]
        items = bits[1:-2]
        return CreateListNode(items, varname)
    else:
        raise template.TemplateSyntaxError('%r expected format is "item [item ...] as varname"' % bits[0])


class CreateListNode(template.Node):
    def __init__(self, items, varname):
        self.items = map(template.Variable, items)
        self.varname = varname

    def render(self, context):
        result = []
        for i in self.items:
            element = i.resolve(context)
            if type(element) is list:
                result.extend(element)
            else:
                result.append(element)
        context[self.varname] = result
        return ''


@register.simple_tag(takes_context=True)
def load_urlpatterns(context):
    from sadiki.anonym.urls import urlpatterns as anonym_patterns
    from sadiki.account.urls import urlpatterns as account_patterns
    from sadiki.authorisation.urls import urlpatterns as auth_patterns
    from sadiki.operator.urls import urlpatterns as operator_patterns
    from sadiki.supervisor.urls import urlpatterns as supervisor_patterns
    from sadiki.statistics.urls import urlpatterns as statictics_patterns
    from sadiki.logger.urls import urlpatterns as logger_patterns
    from sadiki.distribution.urls import urlpatterns as distribution_patterns
    from sadiki.core.urls import urlpatterns as core_patterns

    all_patterns = anonym_patterns + auth_patterns + operator_patterns \
                   + supervisor_patterns + statictics_patterns + account_patterns \
                   + logger_patterns + distribution_patterns + core_patterns
    extra_context = {}

    for pattern in all_patterns:
        try:
            extra_context[pattern.name] = reverse(pattern.name)
        except NoReverseMatch:
            pass

    context.update(extra_context)
    return u''


@register.simple_tag(takes_context=True)
def load_settings(context):
    context.update({'settings': settings})
    return u''


@register.filter
def resolve_url_name(path):
    u""""
    возвращает имя для переданного пути. используется в меню для урлов с параметрами
    """
    try:
        return resolve(path).url_name
    except Resolver404:
#        если не удалось получить(например url flatpages)
        return ''


class ResolveUrlName(Tag):
    options = Options(
        Argument('url', required=True),
        'as',
        Argument('varname', required=True, resolve=False)
    )

    def render_tag(self, context, url, varname):
        result = resolve_url_name(url)
        context[varname] = result
        return ''

register.tag(ResolveUrlName)


class SadikGroupsForRequestion(Tag):
    options = Options(
        Argument('requestion', required=True),
        Argument('sadik', required=True),
        'as',
        Argument('varname', required=True)
    )

    def render_tag(self, context, requestion, sadik, varname):
        result = requestion.get_sadik_groups(sadik)
        context[varname] = result
        return ''

register.tag(SadikGroupsForRequestion)


@register.filter
def appropriate_for_birth_date(sadik_group, birth_date):
    return sadik_group.appropriate_for_birth_date(birth_date)


@register.filter
def multiply(string, times):
    return string * times

class QueueTooltips(Tag):
    options = Options(
        'as',
        Argument('varname', required=True, resolve=False)
    )

    def render_tag(self, context, varname):
        def get_tooltip(template_name, context=None):
            tooltip = render_to_string(template_name, context)
            return mark_safe(re.sub(r'\n', '', tooltip))
        tooltips = {}
        tooltips.update({"requestion_number_tooltip": get_tooltip(
            "core/tooltips/requestion_number_tooltip.html", {'STATIC_URL': settings.STATIC_URL})})
        tooltips.update({"age_groups_tooltip": get_tooltip(
            "core/tooltips/age_groups_tooltip.html",
            {'age_groups': AgeGroup.objects.all()})})
        tooltips.update({"requestion_status_tooltip": get_tooltip(
            "core/tooltips/requestion_status_tooltip.html")})
        tooltips.update({"benefit_categories_tooltip": get_tooltip(
            "core/tooltips/benefit_categories_tooltip.html",
            {'benefit_categories': BenefitCategory.objects.all().order_by('-priority')})})
        context[varname] = tooltips
        return ''

register.tag(QueueTooltips)


@register.filter
def get_field_verbose_name(instance, arg):
    return capfirst(instance._meta.get_field(arg).verbose_name)