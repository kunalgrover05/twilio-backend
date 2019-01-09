# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.admin.views.decorators import staff_member_required
from django.forms import forms, fields
from django.http import HttpResponse
from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, serializers, filters
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.response import Response

from core import models
import logging

from core.serializers import CustomerSMSSerializer, SMSSerializer, MessageTemplateSerializer, TagSerializer, \
    CustomerSerializer, SendSMSSerializer


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
def incoming_message(request):
    body = str(request.POST['Body'])
    sid = request.POST['MessageSid']
    status = request.POST['SmsStatus']
    sender_number = request.POST['To']
    customer = models.Customer.objects.get(phone_number=request.POST['From'])
    logging.error("SMSID %s %s" % (body, sid))
    models.SMS.create_in(sid, sender_number, status, customer, body)
    return HttpResponse(200)


class SendMessageView(CreateAPIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = SendSMSSerializer

    def perform_create(self, serializer):
        serializer.save(sent_by=self.request.user)


class CustomerView(CreateAPIView, UpdateAPIView,
                   RetrieveAPIView, ListAPIView):
    serializer_class = CustomerSerializer
    queryset = models.Customer.objects.all()

    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('pk'):
            return self.list(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)



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


class TagView(CreateAPIView, UpdateAPIView,
                RetrieveAPIView, ListAPIView):
    serializer_class = TagSerializer
    queryset = models.Tag.objects.all()

    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('pk'):
            return self.list(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)


class MessageTemplateView(CreateAPIView, UpdateAPIView,
                RetrieveAPIView, ListAPIView):
    serializer_class = MessageTemplateSerializer
    queryset = models.MessageTemplate.objects.all()

    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('pk'):
            return self.list(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)


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
                                           phone_number='+1' + str(int(sh.row(rx)[1].value)),
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
