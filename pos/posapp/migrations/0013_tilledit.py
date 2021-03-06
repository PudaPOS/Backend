# Generated by Django 3.0.2 on 2020-02-22 09:18

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('posapp', '0012_auto_20200220_2144'),
    ]

    operations = [
        migrations.CreateModel(
            name='TillEdit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=3, default=0, max_digits=15)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('reason', models.TextField()),
                ('count', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posapp.TillMoneyCount')),
            ],
        ),
    ]
