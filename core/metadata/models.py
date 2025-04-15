from django.db import models
from rest_framework import status
from rest_framework.response import Response



# Create your models here.
class Coasts(models.Model):
    """Model definition for Coasts."""
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=20)
    description = models.TextField()

    class Meta:
        verbose_name = 'Coast'
        verbose_name_plural = 'Coasts'
        db_table = 'coasts'

    def __str__(self):
        return self.name

class Departments(models.Model): 
    """Model definition for Departments."""
    coast = models.ForeignKey(Coasts, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=5)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        db_table = 'departments'

    def __str__(self):
        return self.name

class Disciplines(models.Model):
    """Model definition for Disciplines."""
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=20)
    description = models.TextField()

    class Meta:
        verbose_name = 'Discipline'
        verbose_name_plural = 'Disciplines'
        db_table = 'disciplines'

    def __str__(self):
        return self.name
    
class MeasurementUnits(models.Model):
    """Model definition for MeasurementUnits."""
    discipline = models.ForeignKey(Disciplines, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=5)
    symbol = models.CharField(max_length=20, null=True)
    description = models.TextField(null=True)

    class Meta:
        verbose_name = 'MeasurementUnit'
        verbose_name_plural = 'MeasurementUnits'
        db_table = 'measurement_units'

    def __str__(self):
        return str(self.name)  

class ProcessingLevels(models.Model):
    """Model definition for ProcessingLevels."""
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=5)
    level = models.SmallIntegerField()
    description = models.TextField()

    class Meta:
        verbose_name = 'ProcessingLevel'
        verbose_name_plural = 'ProcessingLevels'
        db_table = 'processing_levels'

    def __str__(self):
        return self.name
    
class SamplingRates(models.Model):
    """Model definition for SamplingRates."""
    name = models.CharField(max_length=50)
    value = models.FloatField()
    description = models.TextField()

    class Meta:
        verbose_name = 'SamplingRate'
        verbose_name_plural = 'SamplingRates'
        db_table = 'sampling_rates'

    def __str__(self):
        return self.name                 

class CecoldoCodes(models.Model):
    """Model definition for CecoldoCodes."""
    parameter = models.CharField(max_length=50)
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=250)  # Corregido: 'tittle' a 'title'

    class Meta:
        verbose_name = 'CecoldoCode'
        verbose_name_plural = 'CecoldoCodes'
        db_table = 'cecoldo_codes'

    def __str__(self):
        return self.parameter
    
class QualityFactors(models.Model):
    """Model definition for QualityFactors."""
    name = models.CharField(max_length=50)
    quality_flag = models.CharField(max_length=50)
    description = models.CharField(max_length=250)

    class Meta:
        verbose_name = 'QualityFactor'
        verbose_name_plural = 'QualityFactors'
        db_table = 'quality_factors'

    def __str__(self):
        return self.name 
            
