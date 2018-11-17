from django.contrib import admin
from .models import Attraction, ChargingStation, Hotel, Waypoint

admin.site.register(Attraction)
admin.site.register(ChargingStation)
admin.site.register(Hotel)
admin.site.register(Waypoint)
