# Generated by Django 4.0.4 on 2024-03-09 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_alter_student_student_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='facultyKey',
            field=models.TextField(default='', max_length=1000),
        ),
    ]