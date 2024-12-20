# Generated by Django 5.1.2 on 2024-10-22 09:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('NETFLIX', '0002_rename_name_description_content_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='interval',
            field=models.CharField(choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly', max_length=10),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='plan_type',
            field=models.CharField(choices=[('Basic', 'Basic'), ('Standard', 'Standard'), ('Premium', 'Premium')], default='Basic', max_length=10),
        ),
        migrations.AlterField(
            model_name='description',
            name='plan',
            field=models.ForeignKey(default=' ', on_delete=django.db.models.deletion.CASCADE, related_name='descriptions', to='NETFLIX.subscriptionplan'),
        ),
    ]
