from django.db import models
from metadata.models import Departments,CecoldoCodes,QualityFactors
from variables.models import Variables

# Create your models here.
class Measurements(models.Model):
    department = models.ForeignKey("metadata.Departments", on_delete=models.CASCADE)
    date_time = models.DateField()
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10)
    latitude = models.FloatField()
    longitude = models.FloatField()
    operator = models.CharField(max_length=100)
    description = models.TextField()
    chief_maneuver = models.CharField(max_length=30)

    class Meta:
        db_table = 'measurements'

    def __str__(self):
        return f'{self.name} ({self.date_time})'
    

class ProfileData(models.Model):
    process_descriptor = models.FloatField(null=True, default= 0000)  
    quality_factor = models.ForeignKey(QualityFactors, on_delete=models.PROTECT, null=True)
    depth_marker = models.FloatField()
    variable = models.ForeignKey(Variables, on_delete=models.PROTECT)
    variable_value = models.FloatField()
    timestamp = models.DateTimeField()
    

    class Meta:
        """Meta definition for TimeSeries."""

        verbose_name = 'ProfileData'
        verbose_name_plural = 'ProfileDatas'
        db_table = 'profile_data'

    def __str__(self):
        """Unicode representation of UsedSensors."""
        return f'{self.variable.name}, prof: ({self.depth_marker}), {self.variable.sensor.measurement.name}'

    def save(self, *args, **kwargs):
        """Save method for UsedSensors."""

        super().save(*args, **kwargs)    