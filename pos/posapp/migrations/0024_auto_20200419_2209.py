# Generated by Django 3.0.4 on 2020-04-19 22:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posapp', '0023_tabtransferrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productintab',
            name='orderedAt',
            field=models.DateTimeField(default=datetime.datetime.now, editable=False),
        ),
    ]