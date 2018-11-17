from django.contrib import admin
from .models import Attraction, ChargingStation, Hotel

admin.site.register(Attraction)
admin.site.register(ChargingStation)
admin.site.register(Hotel)
