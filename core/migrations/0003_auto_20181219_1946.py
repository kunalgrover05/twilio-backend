# Generated by Django 2.1.4 on 2018-12-19 19:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20181219_0925'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sms',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='all_sms', to='core.Customer'),
        ),
    ]
