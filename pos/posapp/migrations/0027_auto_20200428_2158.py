# Generated by Django 3.0.5 on 2020-04-28 21:58

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('posapp', '0026_auto_20200428_2151'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TillPaymentOptions',
            new_name='Deposit',
        ),
    ]
