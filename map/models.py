from django.db import models


class Attraction(models.Model):
    name = models.CharField(max_length=255, blank=False)
    lat = models.FloatField(blank=False)
    lon = models.FloatField(blank=False)
    type = models.CharField(max_length=128, blank=False)
    description = models.TextField(max_length=2000, blank=True)


class Hotel(models.Model):
    name = models.CharField(max_length=255, blank=False)
    lat = models.FloatField(blank=False)
    lon = models.FloatField(blank=False)
    rate = models.IntegerField(blank=True, default=0)
    description = models.TextField(max_length=2000, blank=True)


class ChargingStation(models.Model):
    name = models.CharField(max_length=255, blank=False)
    lat = models.FloatField(blank=False)
    lon = models.FloatField(blank=False)
    description = models.TextField(max_length=2000, blank=True)
    voltage = models.IntegerField(blank=True, default=248)
    amperage = models.IntegerField(blank=True, default=96)


class Waypoint(models.Model):
    lat = models.DecimalField(max_digits=10, decimal_places=7, blank=False)
    lon = models.DecimalField(max_digits=10, decimal_places=7, blank=False)