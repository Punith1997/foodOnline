# Generated by Django 3.2.5 on 2022-08-16 14:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_alter_fooditem_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fooditem',
            name='category',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='menu.category'),
        ),
    ]
