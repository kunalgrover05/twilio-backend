import random

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from twilio.rest import Client

from core import models


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

    def validate(self, attrs):
        # User should not get same message twice
        if attrs['customer'].first_sms and attrs['customer'].first_sms.message == attrs['message']:
            raise ValidationError(detail='Already sent this message to this user')

        return super(SendSMSSerializer, self).validate(attrs)

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

        # Replace user attributes in message
        message = validated_data['message'].replace("<Name>", validated_data['customer'].first_name)
        message = message.replace('<Address>', validated_data['customer'].street_address or "")
        message = message.replace('<City>', validated_data['customer'].city or "")
        message = message.replace('<State>', validated_data['customer'].state or "")

        response = client.messages.create(
            body=message,
            to=str(validated_data['customer'].phone_number), from_=sender_number,
            status_callback='https://dxrgulff1k.execute-api.us-east-1.amazonaws.com/dev/callback/')

        return models.SMS.create_og(response.sid,
                             status=response.status,
                             sender_number=sender_number,
                             sent_by=validated_data['sent_by'],
                             customer=validated_data['customer'],
                             message=message)

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = '__all__'


class SMSSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(source='customer.first_name')
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


class CustomerSMSSerializer(serializers.ModelSerializer):
    latest_sms = SMSSerializer(read_only=True)

    class Meta:
        model = models.Customer
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = '__all__'


class MessageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MessageTemplate
        fields = '__all__'


class CustomerSMSFullSerializer(serializers.ModelSerializer):
    all_sms = SMSSerializer(many=True)

    class Meta:
        model = models.Customer
        fields = '__all__'


class CustomerSMSExportSerializer(serializers.ModelSerializer):
    all_sms = SMSSerializer(many=True)
    tag = serializers.StringRelatedField(source='tag.name')

    class Meta:
        model = models.Customer
        exclude = ('latest_sms', )
