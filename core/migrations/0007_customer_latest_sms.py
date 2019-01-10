# Generated by Django 2.1.4 on 2019-01-10 09:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    def add_latest_sms(apps, schema_editor):
        SMS = apps.get_model('core', 'SMS')
        Customer = apps.get_model('core', 'Customer')

        # get latest SMS
        for customer in Customer.objects.all():
            customer.latest_sms = customer.all_sms.order_by('-created').first()
            customer.save()

    dependencies = [
        ('core', '0006_auto_20190104_1838'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='latest_sms',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='customer_last', to='core.SMS'),
        ),

        migrations.RunPython(
            add_latest_sms,
            lambda x,y: None
        )
    ]
