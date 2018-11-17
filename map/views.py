import xml.etree.ElementTree as xml

from django.shortcuts import render
from .forms import UserInputForm

from .models import Attraction, ChargingStation, Hotel
from .Route import Route


def populate_database(request):
    Attraction.objects.all().delete()
    Hotel.objects.all().delete()
    ChargingStation.objects.all().delete()


    e = xml.parse('map/database.osm').getroot()

    for node in e.findall('node'):
        name = ""
        default_station_name = "Charging Station"
        lat = node.attrib["lat"]
        lon = node.attrib["lon"]
        description = ""
        attraction_type = ""
        rate = 0
        voltage = 120
        amperage = 5

        attraction = False
        hotel = False
        chargingStation = False

        # get type
        for tag in node:
            if tag.attrib["k"] == "name":
                name = tag.attrib["v"]

            if tag.attrib["k"] == "amenity" and tag.attrib["v"] == "charging_station":
                name = default_station_name
                chargingStation = True

            if tag.attrib["k"] == "tourism" and tag.attrib["v"] == "hotel":
                hotel = True

            if tag.attrib["k"] == "tourism" and tag.attrib["v"] != "hotel":
                attraction = True

        # set variables
        if name != "":
            if chargingStation:
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "voltage":
                        voltage = tag.attrib["v"]

                    if tag.attrib["k"] == "amperage":
                        amperage = tag.attrib["v"]

                ChargingStation.objects.create(name=name, lat=lat, lon=lon, description=description, voltage=voltage, amperage=amperage)
            elif hotel:
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "stars":
                        rate = tag.attrib["v"]

                Hotel.objects.create(name=name, lat=lat, lon=lon, rate=rate, description=description)

            elif attraction:
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "tourism":
                        attraction_type = tag.attrib["v"]
                Attraction.objects.create(name=name, lat=lat, lon=lon, description=description, type=attraction_type)

    print("Database Populated Successfully")
    return render(request, "index.html", {'form': UserInputForm()})


def index(request):
    if request.method == 'POST':
        form = UserInputForm(request.POST)
    else:
        form = UserInputForm()

    stops = []

    if form.is_valid():
        source = form.cleaned_data['startingPlace']
        destination = form.cleaned_data['destinationPlace']
        max_hops = form.cleaned_data['maxNumberOfStops']
        max_hours = form.cleaned_data['numberOfHours']
        route = Route(source, destination, max_hops, max_hours)
        stops = route.start()

        print(stops)

    return render(request, "index.html", {'form': form,
                                          'stops': stops})
