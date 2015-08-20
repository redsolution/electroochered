# -*- coding: utf-8 -*- 
from django.conf.urls import patterns, url
from forms import LoginForm

# django generic views
from sadiki.authorisation.views import password_set, EmailVerification, \
    send_confirm_letter, login_with_error_handling

urlpatterns = patterns(
    'django.contrib.auth.views',
    url(r'^passwd/$', 'password_change',
        {'template_name': 'authorisation/passwd.html'}, name='passwd'),
    url(r'^passwd/done/$', 'password_change_done',
        {'template_name': 'authorisation/passwd_done.html'},
        name='password_change_done'),
    url(r'^logout/$', 'logout', {'next_page': '/', }, name="logout"),
)

urlpatterns += patterns(
    '',
    url(r'^login/$', login_with_error_handling, {
        'template_name': 'authorisation/login.html',
        'authentication_form': LoginForm}, name='login'),
    url(r'^passwd_set/$', password_set, name='passwd_set'),
    url(r'^send_confirm/$', send_confirm_letter, name='send_confirm_letter'),
    url(r'^email_verification/(?P<key>\w{40})/$',
        EmailVerification.as_view(), name='email_verification'),
    # url(r'^reset_password_request/$',
    #     ResetPasswordRequest.as_view(), name='reset_password_request'),
    # url(r'^reset_password/(?P<key>\w{40})/$',
    #     ResetPassword.as_view(), name='reset_password'),

)
