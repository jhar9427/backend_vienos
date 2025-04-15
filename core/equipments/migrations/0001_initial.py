# Generated by Django 5.1.4 on 2025-03-12 22:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Equipments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('sensor_model', models.CharField(max_length=50)),
                ('sensor_serial', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
            options={
                'db_table': 'equipments',
            },
        ),
        migrations.CreateModel(
            name='MaintenancesDates',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('news', models.CharField(max_length=400)),
            ],
            options={
                'verbose_name': 'MaintenanceDate',
                'verbose_name_plural': 'MaintenanceDates',
                'db_table': 'maintenances_dates',
            },
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('environment_state', models.TextField()),
                ('configutation_filel', models.FileField(blank=True, null=True, upload_to='configurations/')),
                ('alpha', models.FloatField()),
                ('beta', models.FloatField()),
                ('loop_edit_min_velocity', models.FloatField()),
                ('bin_average_type', models.FloatField()),
                ('bin_average_scans_to_skip_over', models.FloatField(default=0)),
                ('bin_average_scans_to_omit', models.FloatField(default=0)),
                ('bin_average_min_scans', models.FloatField(default=0)),
                ('bin_average_max_scans', models.FloatField(default=0)),
                ('cast_to_process', models.CharField(max_length=50)),
                ('filter', models.CharField(max_length=30)),
                ('low_pass_a', models.FloatField()),
                ('low_pass_b', models.FloatField()),
                ('derive', models.CharField()),
                ('cell_thermal', models.FloatField()),
            ],
            options={
                'verbose_name': 'setting',
                'verbose_name_plural': 'settings',
                'db_table': 'settings',
            },
        ),
    ]
