# Generated by Django 5.1.6 on 2025-03-11 12:41

import ckeditor.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SportMeetApp', '0010_remove_rating_user_rating_customer'),
    ]

    operations = [
        migrations.CreateModel(
            name='CancellationAndRefund',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cancellationpolicy', ckeditor.fields.RichTextField(blank=True, null=True)),
                ('refundpolicy', ckeditor.fields.RichTextField(blank=True, null=True)),
                ('venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='SportMeetApp.venue')),
            ],
        ),
    ]
