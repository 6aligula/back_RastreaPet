# Generated by Django 4.1.3 on 2024-04-16 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pet',
            name='missingDate',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
