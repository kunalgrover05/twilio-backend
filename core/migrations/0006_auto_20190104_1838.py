# Generated by Django 2.1.4 on 2019-01-04 18:38

from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20181221_1116'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sms',
            options={'ordering': ['-created']},
        ),
        migrations.AddField(
            model_name='sms',
            name='sender_number',
            field=phonenumber_field.modelfields.PhoneNumberField(default='+13852471760', max_length=128),
            preserve_default=False,
        ),
    ]
