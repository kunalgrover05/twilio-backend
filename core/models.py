# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
from phonenumber_field.modelfields import PhoneNumberField

class Customer(models.Model):
    phone_number = PhoneNumberField(unique=True)
    name = models.CharField(max_length=191)
    street_address = models.CharField(max_length=191, null=True, blank=True)
    city = models.CharField(max_length=191, null=True, blank=True)
    state = models.CharField(max_length=191, null=True, blank=True)
    zip_code = models.PositiveIntegerField(null=True, blank=True)
    contact_list = models.CharField(max_length=191, null=True, blank=True)
    tag = models.ForeignKey('Tag', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class SMS(models.Model):
    sid = models.CharField(max_length=34, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    type = models.CharField(choices=[
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing')
    ], max_length=10)
    sent_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='all_sms')
    message = models.TextField()

    @staticmethod
    def create_og(sid, status, sent_by, customer, message):
        sms = SMS(sid=sid, sent_by=sent_by, customer=customer, message=message, type='outgoing')
        sms.full_clean()
        sms.save()

        smsStatus, c = SMSStatus.objects.get_or_create(sid=sid)
        smsStatus.status = status
        smsStatus.save()

        return sms

    @staticmethod
    def create_in(sid, status, customer, message):
        sms = SMS(sid=sid, customer=customer, message=message, type='incoming')
        sms.full_clean()
        sms.save()

        smsStatus, c = SMSStatus.objects.get_or_create(sid=sid)
        smsStatus.status = status
        smsStatus.save()

        return sms

class SMSStatus(models.Model):
    sid = models.CharField(max_length=34, primary_key=True)
    status = models.CharField(choices=[
        ('accepted', 'Accepted'),
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
        ('undelivered', 'Undelivered'),
        ('receiving', 'Receiving'),
        ('received', 'Received')
    ], max_length=20)


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.name

class MessageTemplate(models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text
