from django.db import models

from metadata.models import SamplingRates,ProcessingLevels,MeasurementUnits

# Create your models here.
class Variables(models.Model):
    """Model definition for Variables."""
    sensor = models.ForeignKey("equipments.Equipments", on_delete=models.CASCADE)
    sampling_rate = models.ForeignKey(SamplingRates, on_delete=models.PROTECT)
    processing_level = models.ForeignKey(ProcessingLevels, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=30)
    #min_value_filter = models.FloatField()
    #max_value_filter = models.FloatField()
    measurement_unit = models.ForeignKey(MeasurementUnits, on_delete=models.CASCADE)
    align_ctd = models.FloatField(default=0)
    description = models.TextField(null=True)

    class Meta:
        verbose_name = 'Variable'
        verbose_name_plural = 'Variables'
        db_table = 'variables'

    def __str__(self):
        return f"{self.name} ({self.sensor.measurement.name})"