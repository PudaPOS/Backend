# Generated by Django 3.0.4 on 2020-04-16 19:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posapp', '0020_auto_20200321_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordervoidrequest',
            name='order',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='posapp.ProductInTab'),
        ),
    ]
