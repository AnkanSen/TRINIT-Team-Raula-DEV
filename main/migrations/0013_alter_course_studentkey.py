# Generated by Django 4.0.4 on 2024-03-09 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_alter_course_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='studentKey',
            field=models.IntegerField(),
        ),
    ]