# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import InvalidPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils.http import urlquote, urlencode
from django.utils.translation import ugettext as _
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from ordereddict import OrderedDict
from sadiki.anonym.forms import PublicSearchForm, RegistrationForm, \
    QueueFilterForm
from sadiki.conf_settings import SPECIAL_TRANSITIONS
from sadiki.core.exceptions import RequestionHidden
from sadiki.core.models import Requestion, Sadik, STATUS_REQUESTER, \
    STATUS_ON_DISTRIBUTION, AgeGroup, STATUS_DISTRIBUTED, STATUS_DECISION, \
    BenefitCategory, Profile, PREFERENCE_IMPORT_FINISHED, Preference, STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE, STATUS_REQUESTER_NOT_CONFIRMED, DISTRIBUTION_PROCESS_STATUSES
from sadiki.core.permissions import RequirePermissionsMixin
from sadiki.core.utils import get_current_distribution_year
from sadiki.core.workflow import CREATE_PROFILE
from sadiki.logger.models import Logger


class Frontpage(RequirePermissionsMixin, TemplateView):
    template_name = 'anonym/frontpage.html'


class Registration(RequirePermissionsMixin, TemplateView):
    u"""Регистрация пользователя в системе"""
    template_name = 'anonym/registration.html'

    def get(self, request, *args, **kwargs):
        registration_form = RegistrationForm()
        context = {'registration_form': registration_form,}
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        registration_form = RegistrationForm(request.POST)
        if registration_form.is_valid():
            user = registration_form.save()
            #        задаем права
            permission = Permission.objects.get(codename=u'is_requester')
            user.user_permissions.add(permission)
            profile = Profile.objects.create(user=user)
            user.set_username_by_id()
            user.save()
            user = authenticate(username=user.username,
                    password=registration_form.cleaned_data['password1'])
            if user is not None:
                if user.is_active:
                    login(request, user)
            Logger.objects.create_for_action(CREATE_PROFILE,
                context_dict={'user': user, 'profile': profile},
                extra={'user': request.user, 'obj': profile})
            return HttpResponseRedirect(reverse('frontpage'))
        else:
            context = {'registration_form': registration_form,}
            return self.render_to_response(context)


class Queue(RequirePermissionsMixin, ListView):
    u"""Отображение очереди в район"""
    template_name = 'anonym/queue.html'
    queryset = Requestion.objects.add_distributed_sadiks(
        # TODO: ОЧЕНЬ долго работает.
        ).select_related('benefit_category__priority').prefetch_related('areas')
    paginate_by = 200
    form = QueueFilterForm
    requestion = None  # Заявка, найденная через форму поиска
    hidden_requestion = None  # Заявка, введенная в форму поиска, но скрытая фильтром

    def paginate_queryset(self, queryset, page_size, page):
        """
        Paginate the queryset, if needed.
        """
        paginator = self.get_paginator(queryset, page_size, allow_empty_first_page=self.get_allow_empty())

        if page is None:
            if self.requestion:
                page = (self.queryset.requestions_before(self.requestion).count() / page_size) + 1
            else:
                # Номер страницы по умолчанию 1
                page = 1

        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_(u"Page is not 'last', nor can it be converted to an int."))


        try:
            page = paginator.page(page_number)
            return paginator, page, page.object_list, page.has_other_pages()
        except InvalidPage:
            raise Http404(_(u'Invalid page (%(page_number)s)') % {
                'page_number': page_number
            })

    def process_filter_form(self, queryset, query_dict):
        u"""Обработчик формы фильтрации заявок"""
        form_data = dict((key, value) for key, value in query_dict.items())
        try:
            form_data.pop('page')
        except KeyError:
            pass
        if form_data:
            form = self.form(query_dict)
            if form.is_valid():
                # Работа с поиском заявки
                initial_queryset = queryset

                # Обработка формы вручную
                if form.cleaned_data.get('confirmed', None):
                    queryset = queryset.confirmed()
                if form.cleaned_data.get('age_group', None):
                    age_group = form.cleaned_data['age_group']
                    queryset = queryset.filter_for_age(min_birth_date=age_group.min_birth_date(),
                                                       max_birth_date=age_group.max_birth_date())
                if form.cleaned_data.get('benefit_category', None):
                    queryset = queryset.filter(benefit_category=form.cleaned_data['benefit_category'])
                area = form.cleaned_data.get('area')
                if area:
                    queryset = queryset.filter(
                        (Q(areas=area) |
                        Q(areas__isnull=True)) & Q(status__in=(STATUS_REQUESTER, STATUS_REQUESTER_NOT_CONFIRMED)) |(
                        Q(distributed_in_vacancy__sadik_group__sadik__area=area)
                        & Q(status__in=DISTRIBUTION_PROCESS_STATUSES+(STATUS_DISTRIBUTED,)))
                    )
                else:
                    queryset = queryset.queue()
                if form.cleaned_data.get('without_facilities'):
                    queryset = queryset.order_by('registration_datetime')

                if form.cleaned_data.get('requestion_number', None):
                    try:
                        self.requestion = queryset.get(requestion_number=form.cleaned_data['requestion_number'])
                    except Requestion.DoesNotExist:
                        try:
                            self.hidden_requestion = initial_queryset.queue().get(
                                requestion_number=form.cleaned_data['requestion_number'])
                            raise RequestionHidden
                        except Requestion.DoesNotExist:
                            messages.add_message(self.request, messages.INFO,
                                u'Заявка с номером %s не найдена' % form.cleaned_data['requestion_number'])
                            raise

                return queryset, form
            else:
                return queryset.queue(), form
        else:
            return queryset.queue(), self.form()

    def get_context_data(self, **kwargs):
        queryset = kwargs.pop('object_list')
        # Отработать форму фильтрации
        page_number = self.request.GET.get('page', None)

        # Обработать фильтры, если они есть
        self.queryset, form = self.process_filter_form(queryset, self.request.GET)

        # Разбить на страницы
        page_size = self.paginate_by
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            self.queryset, page_size, page_number)
#        для всех заявок получаем возрастные группы, которые подходят для них
        age_groups = AgeGroup.objects.all()
        current_distribution_year = get_current_distribution_year()
        for requestion in queryset:
            requestion.age_groups_calculated = requestion.age_groups(
                age_groups=age_groups,
                current_distribution_year=current_distribution_year)
#        для анонимного и авторизованного пользователя нужно отобразить какие особые действия совершались с заявкой
        requestions_dict = OrderedDict([(requestion.id, requestion) for requestion in queryset])
#        нам нужны не все логи, а только с определенными действиями
        if queryset:
#            если получать логи при пустом queryset, то все упадет, паджинатор возвращает queryset[0:0] с пустым query
            logs = Logger.objects.filter(content_type=ContentType.objects.get_for_model(Requestion),
                object_id__in=queryset.values_list('id', flat=True), action_flag__in=SPECIAL_TRANSITIONS)
            relation_dict = {}
            for log in logs:
                requestion_log = relation_dict.get(log.object_id)
    #            если для данной заявки не задан лог или он более старый
                if not requestion_log or requestion_log.datetime < log.datetime:
                    relation_dict[log.object_id] = log
            for id, log in relation_dict.items():
                requestions_dict[id].action_log = log
        context = {
            'paginator': paginator,
            'page_obj': page,
            'is_paginated': is_paginated,
            'requestions_dict': requestions_dict,
            'form': form,
            'target_requestion': self.requestion,
            'offset': (page.number - 1) * page_size,
            'STATUS_DECISION': STATUS_DECISION,
            'NOT_APPEAR_STATUSES': [STATUS_NOT_APPEAR, STATUS_NOT_APPEAR_EXPIRE],
            'STATUS_DISTIRIBUTED': STATUS_DISTRIBUTED,
            'import_finished': Preference.objects.filter(
                key=PREFERENCE_IMPORT_FINISHED).exists()
        }

        context.update(kwargs)
        return context

    def get(self, *args, **kwds):
        u"""
        ``get`` переопределен для того, чтобы если заявка не нашлась по номеру
        из-за того, что выставлены параметры фильтра, которые её скрывают,
        автоматически перенаправлять на страницу безо всяких фильтров
        """
        try:
            response = super(Queue, self).get(*args, **kwds)
        except RequestionHidden:
            return HttpResponseRedirect(u'?' + urlencode({
                'requestion_number': self.hidden_requestion.requestion_number,
            }))
        except Requestion.DoesNotExist:
            return HttpResponseRedirect('.')
        else:
            return response


class RequestionSearch(RequirePermissionsMixin, TemplateView):
    u"""Публичный поиск заявок"""
    template_name = 'anonym/requestion_search.html'
    form = PublicSearchForm
    initial_query = Requestion.objects.queue()
    field_weights = {
        'birth_date__exact': 6,
        'registration_datetime__range': 2,
        'number_in_old_list__exact': 1,
        'id__in': 5,
        'name__icontains': 3,
    }

    def get_context_data(self, **kwargs):
        return {
            'params': kwargs,
            'form': self.form(),
        }

    def guess_more(self, initial_query):
        u"""
        попробуем угадать, какой запрос принесет больше успеха,
        в случае если не найдено ни одной заявки.
        Убираем самый легковесный параметр
        """
#        из всех параметров выбираем с наибольшим весом и смотрим будут ли результаты
        heaviest_key = max(initial_query.keys(), key=lambda x: self.field_weights[x])
        if self.initial_query.filter(
            **{heaviest_key: initial_query[heaviest_key]}).exists():
            # проверка целесообразности уточнения
            new_query = initial_query.copy()
            for _ in initial_query.keys():
                lightest_key = min(new_query.keys(), key=lambda x: self.field_weights[x])
                del new_query[lightest_key]
                more_results = self.initial_query.filter(**new_query)
                if more_results:
                    return new_query, more_results

    def annotate_query(self, query, form):
        params = '&'.join(['%s=%s' % (key, urlquote(value)) for key, value in query.iteritems()])
        annotated = dict(
            original=query,
        )

        annotated['fields'] = {}
        for field in query.keys():
            annotated['fields'][field] = form[form.reverse_field_map[field]]
        return annotated

    def post(self, request, **kwargs):
        form = self.form(request.POST)
        context_data = self.get_context_data(**kwargs)
        context_data['form'] = form
        if form.is_valid():
            query = form.build_query()
            results = self.initial_query.filter(**query)
            context_data.update({
                'query': self.annotate_query(query, form),
                'results': results,
            })
            if results:
                return self.render_to_response(context_data)
            else:
                guess = self.guess_more(query)
                if guess:
                    less_query, more_results = guess
                    context_data.update({
                        'less_query': self.annotate_query(less_query, form),
                        'more_results': more_results,
                    })
                    return self.render_to_response(context_data)
                else:
                    return self.render_to_response(context_data)
        else:
            return self.render_to_response(context_data)

class SadikList(RequirePermissionsMixin, TemplateView):
    template_name = 'anonym/sadik_list.html'

    def get(self, request):
        sadik_list = Sadik.objects.all().select_related('address')
        if not request.user.is_anonymous():
            try:
                profile = request.user.get_profile()
            except Profile.DoesNotExist:
                pass
            else:
                if not request.user.is_requester():
                    return self.render_to_response(
                        {'sadik_list': sadik_list.filter_for_profile(profile)})
        return self.render_to_response({'sadik_list': sadik_list.filter(
            active_registration=True)})


class SadikInfo(RequirePermissionsMixin, TemplateView):
    template_name = 'anonym/sadik_info.html'

    def get(self, request, sadik_id):
        sadik = get_object_or_404(Sadik, id=sadik_id)
        requestions = Requestion.objects.filter(pref_sadiks=sadik,
            status__in=(STATUS_REQUESTER, STATUS_ON_DISTRIBUTION)
        )
        lowest_category = BenefitCategory.objects.category_without_benefits()
        requestions_statistics = {
            'prefer_requestions_number': requestions.count(),
            'prefer_benefit_requestions_number': requestions.filter(
                benefit_category__priority__gt=lowest_category.priority).count()
        }
        age_groups = AgeGroup.objects.all()
        requestions_numbers_by_groups = []
        current_distribution_year = get_current_distribution_year()
        for group in age_groups:
            requestions_numbers_by_groups.append(requestions.filter_for_age(
                min_birth_date=group.min_birth_date(current_distribution_year=current_distribution_year),
                max_birth_date=group.max_birth_date(current_distribution_year=current_distribution_year)).count())
       # список распределенных заявок с путевками в работающие группы этого ДОУ
        groups_with_distributed_requestions = sadik.get_groups_with_distributed_requestions()
        return self.render_to_response({
            'sadik': sadik,
            'requestions_statistics': requestions_statistics,
            'requestions_numbers_by_groups': requestions_numbers_by_groups,
            'groups': age_groups,
            'groups_with_distributed_requestions': groups_with_distributed_requestions,
        })
