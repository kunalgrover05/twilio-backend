# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from django.db.models import Q

from core.models import Customer, SMS, Tag, MessageTemplate


from django.contrib import admin


class CustomerContactListFilter(admin.SimpleListFilter):
    title = 'Contact List exists?'
    parameter_name = 'list_exists'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no',  'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(contact_list__isnull=False).exclude(contact_list='')
        if self.value() == 'no':
            return queryset.filter(Q(contact_list__isnull=True) | Q(contact_list__exact=''))


class CustomerSentSMSFilter(admin.SimpleListFilter):
    title = 'Sent SMS?'
    parameter_name = 'sent_sms'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no',  'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(first_sms__isnull=False)
        if self.value() == 'no':
            return queryset.filter(first_sms__isnull=True)


class CustomerAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    list_filter = ('contact_list', CustomerContactListFilter, CustomerSentSMSFilter, 'responded')

    class Meta:
        model = Customer


class SMSAdmin(admin.ModelAdmin):
    list_display = ('sid', 'customer', 'message')
    class Meta:
        model = SMS


class TagAdmin(admin.ModelAdmin):
    class Meta:
        model = Tag


class MessageTemplateAdmin(admin.ModelAdmin):
    class Meta:
        model = MessageTemplate


admin.site.register(Customer, CustomerAdmin)
admin.site.register(SMS, SMSAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(MessageTemplate, MessageTemplateAdmin)

