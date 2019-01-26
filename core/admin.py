# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.contrib import admin

# Register your models here.
from django.contrib.admin import ACTION_CHECKBOX_NAME
from django.db.models import Q
from django.forms import forms, CharField, MultipleHiddenInput
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response

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


class UpdateContactListForm(forms.Form):
    contact_list = CharField(required=True)
    _selected_action = CharField(widget=MultipleHiddenInput)


class CustomerAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    actions = ('update_contact_list', )
    list_filter = ('contact_list', CustomerContactListFilter, CustomerSentSMSFilter, 'responded')

    def update_contact_list(self, request, queryset):
        form = None

        if 'apply' in request.POST:
            form = UpdateContactListForm(request.POST)
            if form.is_valid():
                queryset.update(contact_list=form.cleaned_data['contact_list'])
                self.message_user(request,
                                  "Changed contact list for {} customers".format(queryset.count()))
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = UpdateContactListForm(initial={'_selected_action': request.POST.getlist(ACTION_CHECKBOX_NAME)})

        return render(
            request,
            template_name='admin/update_contact_list_intermediate.html',
            context={'customers': queryset, 'form': form}
        )


    update_contact_list.short_description = "Change the Contact list"

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

