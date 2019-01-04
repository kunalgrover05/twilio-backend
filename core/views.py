# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.forms import forms, fields
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import permissions, serializers, filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from twilio.rest import Client
from rest_framework.views import APIView

from core import models
import logging

@csrf_exempt
def callback(request):

    sid = str(request.POST['MessageSid'])
    status = request.POST['MessageStatus']
    logging.error("SMSID %s %s" % (sid, status))
    obj, c = models.SMSStatus.objects.get_or_create(sid=sid)
    obj.status = status
    obj.save()

    return HttpResponse(200)


@csrf_exempt
def incoming(request):
    body = str(request.POST['Body'])
    sid = request.POST['MessageSid']
    status = request.POST['SmsStatus']
    sender_number = request.POST['To']
    customer = models.Customer.objects.get(phone_number=request.POST['From'])
    logging.error("SMSID %s %s" % (body, sid))
    models.SMS.create_in(sid, sender_number, status, customer, body)
    return HttpResponse(200)

class SendSMSSerializer(serializers.Serializer):
    message = serializers.CharField()
    customer = serializers.PrimaryKeyRelatedField(queryset=models.Customer.objects.all())
    sent_by = serializers.PrimaryKeyRelatedField(read_only=True)
    preferred_number = PhoneNumberField(allow_null=True, required=False, allow_blank=True)
    status = serializers.SerializerMethodField()
    created = serializers.DateTimeField(read_only=True)
    type = serializers.CharField(read_only=True)

    def get_status(self, obj):
        try:
            return models.SMSStatus.objects.get(sid=obj.sid).get_status_display()
        except ObjectDoesNotExist:
            return None

    def create(self, validated_data):
        client = Client(
            settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        sender_number = None
        numbers = client.incoming_phone_numbers.list()
        if validated_data.get('preferred_number', None) is not None:
            for number in numbers:
                if str(validated_data['preferred_number']) == number.phone_number:
                    sender_number = number.phone_number

        if not sender_number:
            sender_number = random.choice(numbers).phone_number

        response = client.messages.create(
            body=validated_data['message'],
            to=str(validated_data['customer'].phone_number), from_=sender_number,
            status_callback='https://dxrgulff1k.execute-api.us-east-1.amazonaws.com/dev/callback/')

        return models.SMS.create_og(response.sid,
                             status=response.status,
                             sender_number=sender_number,
                             sent_by=validated_data['sent_by'],
                             customer=validated_data['customer'],
                             message=validated_data['message'])

class SendMessageView(CreateAPIView):
    # permission_classes = (permissions.IsAdminUser,)
    serializer_class = SendSMSSerializer

    def perform_create(self, serializer):
        serializer.save(sent_by=self.request.user)

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = '__all__'

class CustomerView(CreateAPIView, UpdateAPIView,
                   RetrieveAPIView, ListAPIView):
    serializer_class = CustomerSerializer
    queryset = models.Customer.objects.all()
    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('pk'):
            return self.list(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)

class SMSSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(source='customer.name')
    sent_by = serializers.StringRelatedField(source='sent_by.first_name')
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        try:
            return models.SMSStatus.objects.get(sid=obj.sid).get_status_display()
        except ObjectDoesNotExist:
            return None

    class Meta:
        model = models.SMS
        fields = '__all__'


class SMSView(CreateAPIView, UpdateAPIView,
              RetrieveAPIView, ListAPIView):
    serializer_class = SMSSerializer
    queryset = models.SMS.objects.all()
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('-created',)
    ordering = ('-created',)

    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('pk'):
            return self.list(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)



class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = '__all__'

class TagView(CreateAPIView, UpdateAPIView,
                RetrieveAPIView, ListAPIView):
    serializer_class = TagSerializer
    queryset = models.Tag.objects.all()

    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('pk'):
            return self.list(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)


class MessageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MessageTemplate
        fields = '__all__'

class MessageTemplateView(CreateAPIView, UpdateAPIView,
                RetrieveAPIView, ListAPIView):
    serializer_class = MessageTemplateSerializer
    queryset = models.MessageTemplate.objects.all()

    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('pk'):
            return self.list(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)


class CustomerSMSSerializer(serializers.ModelSerializer):
    last_sms = serializers.SerializerMethodField(read_only=True)

    def get_last_sms(self, obj):
        if obj.all_sms.first() is not None:
            return SMSSerializer().to_representation(obj.all_sms.order_by('-created').first())
        return None

    class Meta:
        model = models.Customer
        fields = '__all__'


class CustomerSMSFullSerializer(serializers.ModelSerializer):
    all_sms = SMSSerializer(many=True)

    class Meta:
        model = models.Customer
        fields = '__all__'

class CustomerSMSView(ListAPIView, RetrieveAPIView):
    serializer_class = CustomerSMSSerializer
    queryset = models.Customer.objects.prefetch_related('all_sms').all()


class CustomerSMSFullView(RetrieveAPIView):
    serializer_class = CustomerSMSFullSerializer
    queryset = models.Customer.objects.prefetch_related('all_sms').all()


class FileUploadForm(forms.Form):
    file = forms.FileField()
    contact_list = fields.CharField(required=False)

@api_view(['GET'])
def contact_lists(request):
    return Response(set(models.Customer.objects.filter(contact_list__isnull=False)
                        .values_list('contact_list', flat=True).all()))

@csrf_exempt
@staff_member_required
def upload_contacts_list(request):
    """
    Upload soil report using Excel using SampleCode = PlanId as Key
    """

    FIELDS = ['Name', 'Phone No', 'Street Address', 'City', 'State', 'Zip Code']

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        failed = []
        completed = []
        if form.is_valid():
            from xlrd import open_workbook
            book = open_workbook(file_contents=request.FILES['file'].read())
            sh = book.sheet_by_index(0)

            contact_list = form.data['contact_list']

            for index, field in enumerate(FIELDS):
                if field != sh.row(0)[index].value:
                    print(sh.row(0)[index].value)
                    return HttpResponse("Missing field in excel, expected fields: " + ', '.join(FIELDS) + "Failed at index: " + str(index))

            for rx in range(1, sh.nrows):
                customer = models.Customer(name=sh.row(rx)[0].value,
                                           phone_number=sh.row(rx)[1].value,
                                           street_address=sh.row(rx)[2].value,
                                           city=sh.row(rx)[3].value,
                                           state=sh.row(rx)[4].value,
                                           zip_code=sh.row(rx)[5].value or None,
                                           contact_list=contact_list)

                try:
                    customer.save()
                    completed.append(customer)
                except Exception as e:
                    failed.append((sh.row(rx), e))

            return render(request, 'core/render_upload_status.html', {
                'completed': completed,
                'total': sh.nrows-1,
                'contact_list': contact_list,
                'failed': failed
            })

    else:
        form = FileUploadForm()
    return render(request, 'core/empty-form.html', {'form': form})
