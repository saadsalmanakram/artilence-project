# Generated by Django 5.1.5 on 2025-01-26 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_message_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='session_id',
            field=models.CharField(max_length=255, null=True),
        ),
    ]