"""twilio URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from rest_framework.authtoken import views

import core.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^customer/((?P<pk>[0-9]+)/)?', core.views.CustomerView.as_view()),
    url(r'^customerSms/(?P<pk>[0-9]+)/', core.views.CustomerSMSFullView.as_view()),
    url(r'^customerSms/$', core.views.CustomerSMSView.as_view()),
    url(r'^customerSmsExport/$', core.views.CustomerSMSFullExportView.as_view()),
    url(r'^sms/((?P<pk>[\w]+)/)?', core.views.SMSView.as_view()),
    url(r'^messageTemplate/((?P<pk>[\w]+)/)?', core.views.MessageTemplateView.as_view()),
    url(r'^tag/((?P<pk>[0-9]+)/)?', core.views.TagView.as_view()),
    url(r'^send_message/', core.views.SendMessageView.as_view()),
    url(r'^callback/', core.views.callback),
    url(r'^incoming/', core.views.incoming_message),
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^uploadContacts/', core.views.upload_contacts_list),
    url(r'^contactList/', core.views.contact_lists)
]
