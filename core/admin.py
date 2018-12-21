# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from core.models import Customer, SMS, Tag, MessageTemplate


class CustomerAdmin(admin.ModelAdmin):
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