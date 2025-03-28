# Generated by Django 5.1.6 on 2025-03-25 13:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SportMeetApp', '0026_remove_booking_coupon_remove_couponusage_coupon_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discount', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=5, null=True, verbose_name='Discount (%)')),
                ('venue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discounts', to='SportMeetApp.venue')),
            ],
        ),
    ]
