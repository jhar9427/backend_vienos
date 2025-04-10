from django.db import models


# Create your models here.
class Equipments(models.Model):
    measurement = models.ForeignKey("measurements.Measurements", on_delete=models.PROTECT)
    name = models.CharField(max_length=30)
    sensor_model = models.CharField(max_length=50)
    sensor_serial = models.CharField(max_length=50)
    description = models.TextField()

    class Meta:
        db_table = 'equipments'

    def __str__(self):
        return f'{self.sensor_model}'
    
class MaintenancesDates(models.Model):
    """Model definition for MaintenancesDates."""
    sensor = models.ForeignKey(Equipments, on_delete=models.CASCADE)
    date = models.DateField()
    news = models.CharField(max_length=400)

    class Meta:
        verbose_name = 'MaintenanceDate'
        verbose_name_plural = 'MaintenanceDates'
        db_table = 'maintenances_dates'

    def __str__(self):
        return str(self.date)
        
class Settings(models.Model):
    """Model definition for TimeSeries."""
    sensor = models.ForeignKey(Equipments, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    environment_state = models.TextField()  # Corregido: 'enviroment_state' a 'environment_state'
    configutation_filel =models.FileField(upload_to='configurations/', null=True, blank=True)
    alpha = models.FloatField()
    beta = models.FloatField()
    loop_edit_min_velocity = models.FloatField()
    bin_average_type = models.FloatField()
    bin_average_scans_to_skip_over =models.FloatField(default=0)
    bin_average_scans_to_omit =models.FloatField(default=0)
    bin_average_min_scans = models.FloatField(default=0)
    bin_average_max_scans = models.FloatField(default=0)
    cast_to_process = models.CharField(max_length=50)
    filter = models.CharField(max_length=30)
    low_pass_a = models.FloatField()
    low_pass_b = models.FloatField()
    derive = models.CharField()
    cell_thermal = models.FloatField()

    class Meta:
        verbose_name = 'setting'
        verbose_name_plural = 'settings'
        db_table = 'settings'

    def __str__(self):
        return f'{self.sensor.measurement.name}'        