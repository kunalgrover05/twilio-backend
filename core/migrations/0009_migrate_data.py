from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    def add_first_sms(apps, schema_editor):
        SMS = apps.get_model('core', 'SMS')
        Customer = apps.get_model('core', 'Customer')

        # get latest SMS
        for customer in Customer.objects.all():
            customer.first_sms = customer.all_sms.order_by('created').first()
            print(customer.id)
            customer.save()

    def add_responded_data(apps, schema_editor):
        SMS = apps.get_model('core', 'SMS')
        Customer = apps.get_model('core', 'Customer')

        # get latest SMS
        for customer in Customer.objects.all():
            customer.responded = customer.all_sms.filter(type='incoming').exists()
            print(customer.id)
            customer.save()

    dependencies = [
        ('core', '0008_auto_20190119_2045'),
    ]

    operations = [
        migrations.RunPython(
            add_first_sms,
            lambda x, y: None
        ),
        migrations.RunPython(
            add_responded_data,
            lambda x, y: None
        )
    ]
