# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.db.models import Count
from django.forms import forms, fields
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, BooleanFilter
from rest_framework import permissions, serializers, filters
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.response import Response
from rest_pandas import PandasView, PandasMixin, PandasSimpleView, PandasBaseRenderer, PandasSerializer

from core import models
import logging

from core.serializers import CustomerSMSSerializer, SMSSerializer, MessageTemplateSerializer, TagSerializer, \
    CustomerSerializer, SendSMSSerializer, CustomerSMSFullSerializer, CustomerSMSExportSerializer


class CustomerPagination(PageNumberPagination):
    page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
               'next': self.get_next_link(),
               'previous': self.get_previous_link()
            },
            'current': self.page.number,
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })


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
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CustomerSerializer
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    queryset = models.Customer.objects.all().order_by('first_name')
    pagination_class = CustomerPagination
    search_fields = ('first_name', 'last_name', 'city', 'phone_number', 'street_address', 'state', 'zip_code')
    filter_fields = ('contact_list', )

    def get(self, request, *args, **kwargs):
        if not self.request.query_params.get('pk'):
            return self.list(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)


class SMSView(CreateAPIView, UpdateAPIView,
              RetrieveAPIView, ListAPIView):
    serializer_class = SMSSerializer
    permission_classes = (permissions.IsAdminUser,)
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
    permission_classes = (permissions.IsAdminUser,)

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


class CustomerFilter(FilterSet):
    no_message = BooleanFilter(field_name='latest_sms', lookup_expr='isnull')

    class Meta:
        model = models.Customer
        fields = ('no_message', 'tag', 'latest_sms__type', 'responded')


class CustomerSMSView(ListAPIView, RetrieveAPIView):
    permission_classes = (permissions.IsAdminUser,)
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, OrderingFilter)
    filterset_class = CustomerFilter
    search_fields = ('first_name', 'last_name', 'city', 'phone_number', 'street_address', 'state', 'zip_code')
    serializer_class = CustomerSMSSerializer
    queryset = models.Customer.objects.select_related('latest_sms').all()
    pagination_class = CustomerPagination
    ordering_fields = ('latest_sms__created', )
    ordering = ('latest_sms__created', )


class CustomerSMSFullView(RetrieveAPIView):
    serializer_class = CustomerSMSFullSerializer
    queryset = models.Customer.objects.prefetch_related('all_sms').all()


def export_report(request):
    request.GET.get('')


class CustomerSMSFullExportView(PandasView):
    serializer_class = CustomerSMSExportSerializer
    queryset = models.Customer.objects.prefetch_related('all_sms').all().order_by('first_name')
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    filterset_class = CustomerFilter
    permission_classes = (permissions.IsAdminUser,)


    # Adds a single step of merging all messages as one
    def transform_dataframe(self, dataframe):
        dataframe['all_sms'] = [CustomerSMSFullExportView.get_merged_sms_field(x) for x in dataframe['all_sms']]
        return dataframe


    @staticmethod
    def get_merged_sms_field(smsList):
        out = ""
        for sms in smsList:
            out += sms['message']
            date_str = datetime.datetime.strptime(sms['created'],  "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%m/%d/%Y, %H:%M')
            out += '\n' + sms['type'] + ' on ' + date_str + ' ' + sms['status']
            out += '\n\n'
        return out


    def get(self, request, *args, **kwargs):
        try:
            return super(CustomerSMSFullExportView, self).get(request, *args, **kwargs)
        except Exception as e:
            print(e)


class FileUploadForm(forms.Form):
    file = forms.FileField()
    contact_list = fields.CharField(required=True)


@api_view(['GET'])
@staff_member_required
def contact_lists(request):
    return Response(set(models.Customer.objects.filter(contact_list__isnull=False)
                        .values_list('contact_list', flat=True).all()))


@csrf_exempt
@staff_member_required
def upload_contacts_list(request):
    """
    Upload soil report using Excel using SampleCode = PlanId as Key
    """

    FIELDS = ['First Name', 'Last Name', 'Phone No', 'Street Address', 'City', 'State', 'Zip Code']

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
                customer = models.Customer(first_name=sh.row(rx)[0].value,
                                           last_name=sh.row(rx)[1].value,
                                           phone_number='+1' + str(int(sh.row(rx)[2].value)),
                                           street_address=sh.row(rx)[3].value,
                                           city=sh.row(rx)[4].value,
                                           state=sh.row(rx)[5].value,
                                           zip_code=sh.row(rx)[6].value or None,
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
    return render(request, 'core/file-upload-form.html', {'form': form})


@api_view(['GET'])
@staff_member_required
def get_smses_sent_with_replies(request):
    start = request.GET['startDate']
    end = request.GET['endDate']

    dates_sms = {}
    dates_received_sms = {}

    for customer in models.Customer.objects.select_related('first_sms')\
        .filter(first_sms__created__range=[start, end]).distinct().all():
        date = customer.first_sms.created.strftime('%Y-%m-%d')
        dates_sms[date] = dates_sms.get(date, 0) + 1
        if customer.responded:
            dates_received_sms[date] = dates_received_sms.get(date, 0) + 1

    resp = []
    # Merge into single response
    for date, total in dates_sms.items():
        resp.append({
            'date': date,
            'total': total,
            'responded': dates_received_sms.get(date, 0)
        })

    return Response(resp)


@api_view(['GET'])
@staff_member_required
def user_sms_data(request):
    start = request.GET['startDate']
    end = request.GET['endDate']

    # Returns
    # No of SMSes sent by a user on a date
    res = models.SMS.objects.filter(created__range=[start, end], type='outgoing')\
        .values('sent_by__username', 'created__date')\
        .annotate(total=Count('sent_by__username'))\
        .order_by('sent_by__username', 'created__date').all()

    return Response(res)
